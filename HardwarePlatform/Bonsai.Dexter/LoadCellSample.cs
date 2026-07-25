using OpenCV.Net;

namespace Bonsai.Dexter
{
    /// <summary>
    /// One load cell reading from the Dexter BLE device.
    /// <see cref="LoadCells"/> is a 1×15 <see cref="Mat"/> of unsigned 16-bit integers,
    /// one column per channel.
    /// </summary>
    public class LoadCellSample
    {
        public LoadCellSample(int packetCounter, ulong timestampMicroseconds, Mat loadCells)
        {
            PacketCounter = packetCounter;
            TimestampMicroseconds = timestampMicroseconds;
            LoadCells = loadCells;
        }

        /// <summary>Sequence number of the logical packet this sample came from.</summary>
        public int PacketCounter { get; }

        /// <summary>Device timestamp in microseconds.</summary>
        public ulong TimestampMicroseconds { get; }

        /// <summary>15×1 Mat (Depth.U16, 1 channel). Row index = load cell channel (0–14).</summary>
        public Mat LoadCells { get; }
    }
}
