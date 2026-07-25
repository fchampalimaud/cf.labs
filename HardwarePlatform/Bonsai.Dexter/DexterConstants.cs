namespace Bonsai.Dexter
{
    internal static class DexterConstants
    {
        public const string DefaultDeviceName = "Dexter";
        public const string ServiceUuid = "a88278d1-7009-4bee-a6f8-e1dc3ff02b92";
        public const string DataCharUuid     = "a88278d2-7009-4bee-a6f8-e1dc3ff02b92";
        public const string DataModeCharUuid = "a88278d5-7009-4bee-a6f8-e1dc3ff02b92";
        public const byte   DataModeBle      = 0x01;
        public const int LoadCellCount = 15;
        public const int ReadingBlockSize = 8 + (LoadCellCount * 2); // 38 bytes per sample
        public const int LogicalPacketHeaderSize = 5;                 // counter(4) + numReadings(1)
        public const int FragmentHeaderSize = 4;                      // total_len(2) + offset(2)
    }
}
