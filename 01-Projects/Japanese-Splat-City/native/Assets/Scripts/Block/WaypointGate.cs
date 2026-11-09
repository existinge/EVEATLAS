// Japanese Splat City — waypoint trigger gate (DRAFT, NOT YET COMPILED).
//
// A trigger volume that captures an evidence frame via FpsAndCapture when the
// player enters it. Tags per docs/WALK_DESIGN.md: junction, servicebend, rejoin
// (spawn is captured by EvidenceDriver at startup).
using UnityEngine;

namespace JapaneseSplatCity.Block
{
    public class WaypointGate : MonoBehaviour
    {
        [Tooltip("Evidence tag passed to FpsAndCapture.Capture (e.g. 'junction').")]
        public string tagName = "waypoint";

        [Tooltip("Delay in seconds before capturing once triggered.")]
        public float delay = 0.15f;

        Tooling.FpsAndCapture _fcap;
        bool _fired;

        void Start()
        {
            _fcap = Object.FindFirstObjectByType<Tooling.FpsAndCapture>();
        }

        void OnTriggerEnter(Collider other)
        {
            if (_fired) return;
            if (other == null) return;
            if (!other.CompareTag("Player")) return;
            _fired = true;
            if (_fcap == null) return;
            if (delay <= 0f)
            {
                _fcap.Capture(tagName);
            }
            else
            {
                Invoke("Fire", delay);
            }
        }

        void Fire()
        {
            if (_fcap != null) _fcap.Capture(tagName);
        }
    }
}
