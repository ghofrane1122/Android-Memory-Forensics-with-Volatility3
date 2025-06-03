import argparse
import json
import os


def patch_profile(profile_fpath: str) -> bool:
    print(f"[+] Patching {profile_fpath}...")

    try:
        if not os.path.isfile(profile_fpath):
            print(f"[-] Error: File '{profile_fpath}' does not exist.")
            return False

        with open(profile_fpath, "r") as file:
            try:
                profile_content = json.load(file)
            except json.JSONDecodeError as e:
                print(f"[-] Error: Invalid JSON in '{profile_fpath}': {e}")
                return False

        if "base_types" not in profile_content:
            print(f"[-] Error: Profile missing 'base_types' key.")
            return False

        # Check if key already exists
        if "long unsigned int" in profile_content["base_types"]:
            print(
                f"[!] Warning: 'long unsigned int' already exists in profile, skipping patch."
            )
            return True

        # Apply patch
        profile_content["base_types"]["long unsigned int"] = {
            "size": 8,
            "signed": False,
            "kind": "int",
            "endian": "little",
        }

        # Write back to file
        try:
            with open(profile_fpath, "w") as file:
                json.dump(profile_content, file, indent=4)
            print(f"[+] Successfully patched {profile_fpath}.")
            return True
        except (IOError, PermissionError) as e:
            print(f"[-] Error: Failed to write to '{profile_fpath}': {e}")
            return False

    except Exception as e:
        print(f"[-] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Patch the btf2json volatility profile."
    )
    argparser.add_argument(
        "-f",
        type=str,
        required=True,
        help="Path to the btf2json vol profile to be patched.",
    )

    args = argparser.parse_args()
    success = patch_profile(args.f)
    exit(0 if success else 1)