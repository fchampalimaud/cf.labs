# Bonsai.Dexter

A Bonsai C# class library that streams load cell data from the **Dexter** BLE peripheral into a Bonsai workflow.

## What it does

The `DexterBleSource` node connects to the Dexter device over Bluetooth LE and emits one `LoadCellSample` per reading block at ~200 Hz (two samples per 80-byte BLE notification).

## Output type — `LoadCellSample`

| Property | Type | Description |
|---|---|---|
| `PacketCounter` | `int` | Incrementing uint16 counter from the device (wraps at 65535) |
| `TimestampMicroseconds` | `ulong` | Device timestamp in microseconds |
| `LoadCells` | `Mat` (15×1, Depth.U16) | One value per load cell channel; row index = channel (0–14) |

## Node properties

| Property | Default | Description |
|---|---|---|
| `DeviceName` | `"Dexter"` | Name prefix used when scanning (fallback if address is cleared) |
| `DeviceAddress` | `"CA2B204E8E0D"` | Hardware Bluetooth address — hardcoded to skip scanning entirely |
| `ScanTimeoutSeconds` | `10.0` | How long to wait during a scan before throwing. `0` = indefinite |

`DeviceAddress` is the static-random BLE MAC address of the physical Dexter unit. Clear it only if connecting to a different device.

## Wire format

The device streams 80-byte UART-mode notifications (not the fragment/BLE-mode protocol used by the Python client):

```
bytes [0..1]   uint16 LE   absolute packet counter
bytes [2..3]   0x0000      reserved
bytes [4..41]              reading block 0: uint64 timestamp_µs + 15×uint16 load cells
bytes [42..79]             reading block 1: uint64 timestamp_µs + 15×uint16 load cells
```

Each reading block is 38 bytes: 8 bytes timestamp + 15×2 bytes load cells.

## BLE UUIDs

| Name | UUID |
|---|---|
| Service | `a88278d1-7009-4bee-a6f8-e1dc3ff02b92` |
| Data characteristic (notify) | `a88278d2-7009-4bee-a6f8-e1dc3ff02b92` |
| Data mode characteristic | `a88278d5-7009-4bee-a6f8-e1dc3ff02b92` |

The data mode characteristic (`a88278d5`) is used by the Python client to switch the device between UART mode and BLE mode. It is not accessible via WinRT GATT (returns count=0), so the C# library always parses UART-mode packets.

## Connection flow

1. If `DeviceAddress` is set, open the device directly via `BluetoothLEDevice.FromBluetoothAddressAsync` — no scan.
2. Otherwise check the Windows BLE device registry (`DeviceInformation.FindAllAsync`) for a cached entry matching `DeviceName`.
3. Fall back to an active advertisement watcher if not found in the registry.
4. After first successful scan the address is cached in a static field for the lifetime of the Bonsai session.
5. Get the service and data characteristic, enable notifications, and emit samples until disconnect or workflow stop.

## Project setup

- Target framework: `net472` (required by Bonsai)
- NuGet references: `Bonsai.Core 2.9.1`, `Bonsai.Dsp 2.9.1`, `Microsoft.Windows.SDK.Contracts 10.0.19041.1`
- F5 in Visual Studio launches `Bonsai.exe --lib <bin/Debug/net472>` via `Properties/launchSettings.json`
- `PackageType = Dependency;BonsaiLibrary` makes the package visible in the Bonsai package manager
