// Japanese Splat City — first-person walk controller for the packaged player.
//
// DRAFT, NOT YET COMPILED: requires the first editor import on a licensed host.
//
// Simple CharacterController rig: mouse look (locked cursor), WASD walk,
// gravity, no jump (enclosed arcade). Esc releases the cursor.
using UnityEngine;

namespace JapaneseSplatCity.Player
{
    [RequireComponent(typeof(CharacterController))]
    public class FpsController : MonoBehaviour
    {
        [Tooltip("Camera attached to this rig (assigned by BlockBuilder or inspector).")]
        public Transform cam;

        public float walkSpeed = 4f;
        public float mouseSensitivity = 2f;
        public float gravityAccel = 24f;

        CharacterController _cc;
        float _pitch;
        float _verticalVel;

        void Awake()
        {
            _cc = GetComponent<CharacterController>();
            if (cam == null && Camera.main != null) cam = Camera.main.transform;
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }

        void Update()
        {
            float mx = Input.GetAxis("Mouse X") * mouseSensitivity;
            float my = Input.GetAxis("Mouse Y") * mouseSensitivity;
            transform.Rotate(0f, mx, 0f, Space.Self);
            _pitch = Mathf.Clamp(_pitch - my, -85f, 85f);
            if (cam != null) cam.localRotation = Quaternion.Euler(_pitch, 0f, 0f);

            Vector3 wish = Vector3.zero;
            if (Input.GetKey(KeyCode.W)) wish += transform.forward;
            if (Input.GetKey(KeyCode.S)) wish -= transform.forward;
            if (Input.GetKey(KeyCode.A)) wish -= transform.right;
            if (Input.GetKey(KeyCode.D)) wish += transform.right;
            if (wish.sqrMagnitude > 1f) wish.Normalize();

            if (_cc.isGrounded)
                _verticalVel = -1f;
            else
                _verticalVel -= gravityAccel * Time.deltaTime;

            _cc.Move(new Vector3(
                wish.x * walkSpeed * Time.deltaTime,
                _verticalVel * Time.deltaTime,
                wish.z * walkSpeed * Time.deltaTime));
        }
    }
}
