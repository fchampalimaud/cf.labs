using System;
using System.Collections.Concurrent;
using System.ComponentModel;
using System.Globalization;
using System.Reactive.Linq;
using System.Threading;
using System.Threading.Tasks;
using Bonsai;
using Windows.Devices.Bluetooth;
using Windows.Devices.Bluetooth.Advertisement;
using Windows.Devices.Bluetooth.GenericAttributeProfile;
using Windows.Devices.Enumeration;
using Windows.Foundation;
using Windows.Storage.Streams;

namespace Bonsai.Dexter
{
    [Description("Streams load cell samples from the Dexter BLE device. Each item is one reading block: a 15×1 Mat (U16) with all 15 channel values and a device timestamp.")]
    public class DexterBleSource : Source<LoadCellSample>
    {
        // Cached address from first successful scan — shared across all instances in the session.
        private static ulong _cachedAddress;

        [Description("Advertised device name prefix to scan for.")]
        public string DeviceName { get; set; } = DexterConstants.DefaultDeviceName;

        [Description("Seconds to scan before giving up. Set to 0 to scan indefinitely.")]
        [DefaultValue(10.0)]
        public double ScanTimeoutSeconds { get; set; } = 10.0;

        [Description("Bluetooth address in hex to bypass scanning. Clear to scan automatically.")]
        [DefaultValue("CA2B204E8E0D")]
        public string DeviceAddress { get; set; } = "CA2B204E8E0D";

        public override IObservable<LoadCellSample> Generate()
        {
            Console.WriteLine("[Dexter] Generate() called");

            return Observable.Create<LoadCellSample>(async (observer, cancellationToken) =>
            {
                Console.WriteLine("[Dexter] Observable subscribed — starting BLE connection");
                BluetoothLEDevice device = null;
                GattDeviceService service = null;
                GattCharacteristic characteristic = null;
                TypedEventHandler<GattCharacteristic, GattValueChangedEventArgs> notifyHandler = null;

                try
                {
                    // --- 1. Resolve address (property → session cache → full scan) ---
                    ulong address;
                    if (!string.IsNullOrWhiteSpace(DeviceAddress) &&
                        ulong.TryParse(DeviceAddress.Replace(":", "").Replace("-", ""),
                                       NumberStyles.HexNumber, null, out var addrFromProp))
                    {
                        address = addrFromProp;
                        Console.WriteLine($"[Dexter] Using configured address: {address:X12}");
                    }
                    else if (_cachedAddress != 0)
                    {
                        address = _cachedAddress;
                        Console.WriteLine($"[Dexter] Using cached address: {address:X12}");
                    }
                    else
                    {
                        Console.WriteLine($"[Dexter] Scanning for '{DeviceName}' (timeout={ScanTimeoutSeconds}s)...");
                        if (ScanTimeoutSeconds > 0)
                        {
                            using var scanCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                            scanCts.CancelAfter(TimeSpan.FromSeconds(ScanTimeoutSeconds));
                            try
                            {
                                address = await ScanForDeviceAsync(DeviceName, scanCts.Token);
                            }
                            catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
                            {
                                throw new TimeoutException(
                                    $"No BLE device matching '{DeviceName}' found within {ScanTimeoutSeconds}s.");
                            }
                        }
                        else
                        {
                            address = await ScanForDeviceAsync(DeviceName, cancellationToken);
                        }
                        _cachedAddress = address;
                        Console.WriteLine($"[Dexter] Device found: {address:X12} (cached for this session)");
                    }

                    // --- 2. Connect ---
                    Console.WriteLine("[Dexter] Opening BLE device...");
                    device = await BluetoothLEDevice.FromBluetoothAddressAsync(address);
                    if (device == null)
                        throw new InvalidOperationException("Could not open BLE device after scanning.");
                    Console.WriteLine($"[Dexter] Opened: name='{device.Name}' status={device.ConnectionStatus}");

                    // --- 3. Get service ---
                    Console.WriteLine($"[Dexter] Getting service {DexterConstants.ServiceUuid}...");
                    var serviceResult = await device.GetGattServicesForUuidAsync(
                        Guid.Parse(DexterConstants.ServiceUuid),
                        BluetoothCacheMode.Uncached);
                    Console.WriteLine($"[Dexter] Service: status={serviceResult.Status} count={serviceResult.Services.Count}");
                    if (serviceResult.Status != GattCommunicationStatus.Success
                        || serviceResult.Services.Count == 0)
                        throw new InvalidOperationException(
                            $"Dexter service not found ({serviceResult.Status}).");
                    service = serviceResult.Services[0];

                    // --- 4. Get characteristic ---
                    Console.WriteLine($"[Dexter] Getting characteristic {DexterConstants.DataCharUuid}...");
                    var charResult = await service.GetCharacteristicsForUuidAsync(
                        Guid.Parse(DexterConstants.DataCharUuid),
                        BluetoothCacheMode.Uncached);
                    Console.WriteLine($"[Dexter] Characteristic: status={charResult.Status} count={charResult.Characteristics.Count}");
                    if (charResult.Status != GattCommunicationStatus.Success
                        || charResult.Characteristics.Count == 0)
                        throw new InvalidOperationException(
                            $"Data characteristic not found ({charResult.Status}).");
                    characteristic = charResult.Characteristics[0];
                    Console.WriteLine($"[Dexter] Characteristic properties: {characteristic.CharacteristicProperties}");

                    // --- 5. Subscribe to notifications ---
                    var reassembler = new PacketReassembler();
                    int notifCount = 0;
                    notifyHandler = (sender, args) =>
                    {
                        var reader = DataReader.FromBuffer(args.CharacteristicValue);
                        var data = new byte[(int)args.CharacteristicValue.Length];
                        reader.ReadBytes(data);

                        notifCount++;
                        // Log first 5, then every 500 to avoid console flood at 200 Hz.
                        if (notifCount <= 5 || notifCount % 500 == 0)
                            Console.WriteLine($"[Dexter] Notification #{notifCount}: {data.Length} bytes");

                        foreach (var sample in reassembler.ConsumeFragment(data))
                            observer.OnNext(sample);
                    };
                    characteristic.ValueChanged += notifyHandler;

                    // --- 6. Enable notifications ---
                    Console.WriteLine("[Dexter] Enabling notifications...");
                    var notifyStatus = await characteristic
                        .WriteClientCharacteristicConfigurationDescriptorAsync(
                            GattClientCharacteristicConfigurationDescriptorValue.Notify);
                    Console.WriteLine($"[Dexter] Notify status: {notifyStatus}");
                    if (notifyStatus != GattCommunicationStatus.Success)
                        throw new InvalidOperationException(
                            $"Failed to enable notifications ({notifyStatus}).");

                    Console.WriteLine("[Dexter] Streaming — waiting for data or disconnect.");

                    // --- 7. Wait for disconnect or workflow stop ---
                    var disconnectTcs = new TaskCompletionSource<bool>();
                    device.ConnectionStatusChanged += (d, _) =>
                    {
                        Console.WriteLine($"[Dexter] Connection status: {d.ConnectionStatus}");
                        if (d.ConnectionStatus == BluetoothConnectionStatus.Disconnected)
                            disconnectTcs.TrySetResult(true);
                    };

                    using (cancellationToken.Register(() => disconnectTcs.TrySetCanceled()))
                    {
                        try { await disconnectTcs.Task; }
                        catch (OperationCanceledException) { }
                    }

                    Console.WriteLine("[Dexter] Streaming ended.");
                }
                catch (OperationCanceledException) { Console.WriteLine("[Dexter] Cancelled."); }
                catch (Exception ex)
                {
                    Console.WriteLine($"[Dexter] ERROR: {ex.GetType().Name}: {ex.Message}");
                    observer.OnError(ex);
                }
                finally
                {
                    Console.WriteLine("[Dexter] Cleaning up...");
                    if (characteristic != null && notifyHandler != null)
                    {
                        characteristic.ValueChanged -= notifyHandler;
                        try
                        {
                            await characteristic.WriteClientCharacteristicConfigurationDescriptorAsync(
                                GattClientCharacteristicConfigurationDescriptorValue.None);
                        }
                        catch { }
                    }
                    service?.Dispose();
                    device?.Dispose();
                    Console.WriteLine("[Dexter] Done.");
                }
            });
        }

        private static async Task<ulong> ScanForDeviceAsync(string name, CancellationToken cancellationToken)
        {
            // Step 1: Check Windows BLE device registry — this is how Bleak resolves device names.
            // FindAllAsync returns every BLE device Windows has cached (paired or previously seen),
            // along with the human-readable name stored in the OS device registry.
            Console.WriteLine("[Dexter] Checking Windows BLE device registry...");
            try
            {
                foreach (bool paired in new[] { true, false })
                {
                    var selector = BluetoothLEDevice.GetDeviceSelectorFromPairingState(paired);
                    var infos = await DeviceInformation.FindAllAsync(selector);
                    Console.WriteLine($"[Dexter] {(paired ? "Paired" : "Unpaired")} BLE devices in registry: {infos.Count}");
                    foreach (var info in infos)
                    {
                        Console.WriteLine($"[Dexter]   {(paired ? "P" : "U")}: '{info.Name}' ({info.Id})");
                        if (info.Name.IndexOf(name, StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            Console.WriteLine($"[Dexter] Matched registry entry: '{info.Name}'");
                            var tempDev = await BluetoothLEDevice.FromIdAsync(info.Id);
                            if (tempDev != null)
                            {
                                ulong addr = tempDev.BluetoothAddress;
                                tempDev.Dispose();
                                return addr;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Dexter] Registry check error: {ex.GetType().Name}: {ex.Message}");
            }

            // Step 2: Fall back to advertisement watcher.
            Console.WriteLine("[Dexter] Not found in registry. Starting advertisement watcher...");
            var tcs = new TaskCompletionSource<ulong>();
            var serviceUuid = Guid.Parse(DexterConstants.ServiceUuid);
            var seen = new ConcurrentDictionary<ulong, byte>();

            var watcher = new BluetoothLEAdvertisementWatcher
            {
                ScanningMode = BluetoothLEScanningMode.Active
            };

            watcher.Received += async (sender, args) =>
            {
                if (tcs.Task.IsCompleted) return;

                var localName = args.Advertisement.LocalName ?? string.Empty;
                var serviceUuids = args.Advertisement.ServiceUuids;
                Console.WriteLine($"[Dexter] Adv: {args.BluetoothAddress:X12} rssi={args.RawSignalStrengthInDBm} name='{localName}' uuids={serviceUuids.Count}");

                // 1. Local name in the advertisement or scan-response packet.
                if (!string.IsNullOrEmpty(localName) &&
                    localName.IndexOf(name, StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    Console.WriteLine($"[Dexter] Matched by local name: '{localName}'");
                    tcs.TrySetResult(args.BluetoothAddress);
                    return;
                }

                // 2. Service UUID in the advertisement.
                if (serviceUuids.Contains(serviceUuid))
                {
                    Console.WriteLine($"[Dexter] Matched by service UUID");
                    tcs.TrySetResult(args.BluetoothAddress);
                    return;
                }

                // 3. OS-cached name via FromBluetoothAddressAsync — only once per address.
                if (seen.TryAdd(args.BluetoothAddress, 0))
                {
                    try
                    {
                        var tempDev = await BluetoothLEDevice.FromBluetoothAddressAsync(args.BluetoothAddress);
                        var cachedName = tempDev?.Name ?? string.Empty;
                        tempDev?.Dispose();
                        Console.WriteLine($"[Dexter] OS cache {args.BluetoothAddress:X12}: name='{cachedName}'");
                        if (cachedName.IndexOf(name, StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            Console.WriteLine($"[Dexter] Matched by OS-cached name: '{cachedName}'");
                            tcs.TrySetResult(args.BluetoothAddress);
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[Dexter] Cache lookup failed: {ex.Message}");
                    }
                }
            };

            watcher.Stopped += (sender, args) =>
                Console.WriteLine($"[Dexter] Watcher stopped. Error={args.Error}");

            Console.WriteLine("[Dexter] Watcher starting...");
            using (cancellationToken.Register(() => tcs.TrySetCanceled()))
            {
                watcher.Start();
                Console.WriteLine($"[Dexter] Watcher status: {watcher.Status}");
                try { return await tcs.Task; }
                finally { watcher.Stop(); }
            }
        }
    }
}
