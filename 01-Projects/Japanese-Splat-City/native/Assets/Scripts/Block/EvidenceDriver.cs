// Japanese Splat City — evidence driver (DRAFT, NOT YET COMPILED).
//
// Wires the FpsAndCapture tooling to the runtime-built block:
//   - tags the player rig's capsule so the waypoint gates trigger,
//   - guarantees an FpsAndCapture component exists (adds one if missing),
//   - captures the "spawn" frame a couple of seconds after start (gates own
//     junction / servicebend / rejoin).
using System.Collections;
using UnityEngine;

namespace JapaneseSplatCity.Block
{
    public class EvidenceDriver : MonoBehaviour
    {
        public float spawnCaptureDelay = 2.0f;
        public bool autoTagPlayer = true;

        Tooling.FpsAndCapture _fcap;

        void Start()
        {
            _fcap = Object.FindFirstObjectByType<Tooling.FpsAndCapture>();
            if (_fcap == null)
            {
                var rig = GameObject.Find("PlayerRig");
                if (rig != null)
                {
                    _fcap = rig.AddComponent<Tooling.FpsAndCapture>();
                    Debug.Log("[EvidenceDriver] added FpsAndCapture to PlayerRig");
                }
            }

            if (autoTagPlayer)
            {
                var capsule = GameObject.Find("PlayerRig");
                if (capsule != null)
                {
                    capsule.tag = "Player";
                    // ensure CharacterController (moved by FpsController) carries the tag
                    var cc = capsule.GetComponent<CharacterController>();
                    if (cc != null) cc.gameObject.tag = "Player";
                }
            }

            StartCoroutine(CaptureSpawn());
        }

        IEnumerator CaptureSpawn()
        {
            yield return new WaitForSeconds(spawnCaptureDelay);
            if (_fcap != null) _fcap.Capture("spawn");
        }
    }
}
