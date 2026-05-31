using System.Net.NetworkInformation;
using System.Timers;

namespace AutoShutdown.Services;

public sealed class NetworkIdleService : IDisposable
{
    private readonly System.Timers.Timer _timer = new(1000);
    private long _lastReceivedBytes;
    private long _lastSentBytes;
    private int _downloadThresholdKb;
    private int _uploadThresholdKb;
    private int _requiredIdleSeconds;
    private int _idleSeconds;
    private bool _running;

    public event Action<double, double, int, int>? Tick;
    public event Action? IdleReached;

    public NetworkIdleService()
    {
        _timer.AutoReset = true;
        _timer.Elapsed += OnTimerElapsed;
    }

    public void Start(int downloadThresholdKb, int uploadThresholdKb, int idleMinutes)
    {
        _downloadThresholdKb = Math.Max(0, downloadThresholdKb);
        _uploadThresholdKb = Math.Max(0, uploadThresholdKb);
        _requiredIdleSeconds = Math.Max(1, idleMinutes) * 60;
        _idleSeconds = 0;
        (_lastReceivedBytes, _lastSentBytes) = GetNetworkBytes();
        _running = true;
        _timer.Start();
    }

    public void Stop()
    {
        _running = false;
        _timer.Stop();
        _idleSeconds = 0;
    }

    private void OnTimerElapsed(object? sender, ElapsedEventArgs e)
    {
        if (!_running)
            return;

        var (receivedBytes, sentBytes) = GetNetworkBytes();
        var downloadKb = Math.Max(0, receivedBytes - _lastReceivedBytes) / 1024d;
        var uploadKb = Math.Max(0, sentBytes - _lastSentBytes) / 1024d;
        _lastReceivedBytes = receivedBytes;
        _lastSentBytes = sentBytes;

        if (downloadKb <= _downloadThresholdKb && uploadKb <= _uploadThresholdKb)
            _idleSeconds++;
        else
            _idleSeconds = 0;

        Tick?.Invoke(downloadKb, uploadKb, _idleSeconds, _requiredIdleSeconds);

        if (_idleSeconds >= _requiredIdleSeconds)
        {
            Stop();
            IdleReached?.Invoke();
        }
    }

    private static (long receivedBytes, long sentBytes) GetNetworkBytes()
    {
        long received = 0;
        long sent = 0;

        foreach (var networkInterface in NetworkInterface.GetAllNetworkInterfaces())
        {
            if (networkInterface.OperationalStatus != OperationalStatus.Up)
                continue;

            if (networkInterface.NetworkInterfaceType is NetworkInterfaceType.Loopback or NetworkInterfaceType.Tunnel)
                continue;

            var stats = networkInterface.GetIPv4Statistics();
            received += stats.BytesReceived;
            sent += stats.BytesSent;
        }

        return (received, sent);
    }

    public void Dispose()
    {
        _timer.Dispose();
    }
}
