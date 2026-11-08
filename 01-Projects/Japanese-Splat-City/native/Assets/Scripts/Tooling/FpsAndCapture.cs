// Japanese Splat City — evidence tooling for the packaged player.
//
// DRAFT, NOT YET COMPILED: requires the first editor import on a licensed host.
//
// Attach to the player rig. Behaviour:
//   - every $sampleWindow seconds logs a row to Player.log and appends one line
//     to fps.csv in the payload folder (next to JapaneseSplatCity.exe)
//   - F12 (or Capture()) writes PNG screenshots into <payload>/Screenshots/
//   - evidence frames (spawn / junction / service-bend / rejoin) are taken by
//     calling Capture("spawn-<route>") from the scene's waypoint triggers.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace JapaneseSplatCity.Tooling
{
    public class FpsAndCapture : MonoBehaviour
    {
        [Tooltip("Seconds per fps summary row.")]
        public float sampleWindow = 5f;
        public KeyCode captureKey = KeyCode.F12;

        float _frames;
        float _timer;
        float _best = float.MinValue;
        float _worst = float.MaxValue;
        readonly List<string> _rows = new List<string>();

        // Payload root = parent of <exe>_Data; keep evidence inside the shipped
        // folder instead of the profile so a sandboxed host can still record it.
        static string PayloadRoot
        {
            get
            {
                var dir = Directory.GetParent(Application.dataPath);
                return dir != null ? dir.FullName : Application.dataPath;
            }
        }

        void Update()
        {
            _frames++;
            float dt = Mathf.Max(Time.unscaledDeltaTime, 1e-6f);
            _timer += dt;
            float fps = 1f / dt;
            if (fps > _best) _best = fps;
            if (fps < _worst) _worst = fps;

            if (_timer >= sampleWindow)
            {
                float avg = _frames / _timer;
                string row = string.Format("{0:F2},{1:F1},{2:F1},{3:F1}",
                    Time.realtimeSinceStartup, avg, _best, _worst);
                _rows.Add(row);
                Debug.Log("[FpsAndCapture] t=" + row + " (elapsed,avgFps,bestFps,worstFps)");
                _frames = 0f;
                _timer = 0f;
                _best = float.MinValue;
                _worst = float.MaxValue;
                Flush();
            }

            if (Input.GetKeyDown(captureKey)) Capture("manual");
        }

        void OnApplicationQuit()
        {
            Flush();
        }

        void Flush()
        {
            if (_rows.Count == 0) return;
            string path = Path.Combine(PayloadRoot, "fps.csv");
            try
            {
                File.AppendAllLines(path, _rows);
                _rows.Clear();
            }
            catch (Exception e)
            {
                Debug.LogWarning("[FpsAndCapture] fps.csv write failed: " + e.Message);
            }
        }

        public void Capture(string tag)
        {
            string dir = Path.Combine(PayloadRoot, "Screenshots");
            try
            {
                Directory.CreateDirectory(dir);
                string name = string.Format("frame-{0}-{1:yyyyMMdd-HHmmss}.png",
                    tag, DateTime.Now);
                ScreenCapture.CaptureScreenshot(Path.Combine(dir, name));
                Debug.Log("[FpsAndCapture] captured " + name);
            }
            catch (Exception e)
            {
                Debug.LogWarning("[FpsAndCapture] screenshot failed: " + e.Message);
            }
        }
    }
}
