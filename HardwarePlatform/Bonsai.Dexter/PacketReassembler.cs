using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using OpenCV.Net;

namespace Bonsai.Dexter
{
    // Parses the 80-byte UART-mode notification format:
    //   [0..1]  uint16 LE  absolute packet counter
    //   [2..3]  0x0000     reserved
    //   [4..41]            reading block 0: uint64 timestamp_µs + 15×uint16 load cells
    //   [42..79]           reading block 1: uint64 timestamp_µs + 15×uint16 load cells
    // Each LoadCellSample.LoadCells is a 15×1 Mat (Depth.U16): row = channel, column = 0.
    internal class PacketReassembler
    {
        private const int PacketSize = 80;
        private const int ReadingSize = DexterConstants.ReadingBlockSize; // 38
        private const int Reading0Offset = 4;
        private const int Reading1Offset = 4 + ReadingSize; // 42

        private int _dumpCount = 0;

        public IEnumerable<LoadCellSample> ConsumeFragment(byte[] data)
        {
            // Hex-dump the first 3 packets so the wire format is visible in the log.
            if (++_dumpCount <= 3)
            {
                var sb = new StringBuilder();
                sb.Append($"[Dexter] Raw[{_dumpCount}] ({data.Length}B): ");
                foreach (var b in data) sb.Append(b.ToString("X2")).Append(' ');
                Console.WriteLine(sb);
            }

            if (data.Length != PacketSize)
            {
                Console.WriteLine($"[Dexter] Unexpected size: {data.Length} (expected {PacketSize}) — skipping");
                yield break;
            }

            int counter = BitConverter.ToUInt16(data, 0);

            var s0 = ParseReadingBlock(data, Reading0Offset, counter);
            if (s0 != null) yield return s0;

            var s1 = ParseReadingBlock(data, Reading1Offset, counter);
            if (s1 != null) yield return s1;
        }

        private static LoadCellSample ParseReadingBlock(byte[] data, int offset, int counter)
        {
            if (offset + ReadingSize > data.Length) return null;

            ulong timestamp = BitConverter.ToUInt64(data, offset);
            var mat = new Mat(DexterConstants.LoadCellCount, 1, Depth.U16, 1);
            Marshal.Copy(data, offset + 8, mat.Data, DexterConstants.LoadCellCount * 2);
            return new LoadCellSample(counter, timestamp, mat);
        }
    }
}
