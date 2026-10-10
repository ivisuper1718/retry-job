# Tries once to create the free server. Prints nothing identifying (logs stay private-safe).
import os, sys
import oci

e = os.environ
cfg = {
    "user": e["OCI_USER"], "fingerprint": e["OCI_FINGERPRINT"], "tenancy": e["OCI_TENANCY"],
    "region": e["OCI_REGION"], "key_content": e["OCI_KEY"],
}
NAME = "free-server"
compute = oci.core.ComputeClient(cfg)


def done():
    with open(e["GITHUB_OUTPUT"], "a") as f:
        f.write("created=true\n")
    sys.exit(0)


existing = oci.pagination.list_call_get_all_results(
    compute.list_instances, e["OCI_TENANCY"], display_name=NAME).data
if any(i.lifecycle_state != "TERMINATED" for i in existing):
    print("Server already exists.")
    done()

details = oci.core.models.LaunchInstanceDetails(
    compartment_id=e["OCI_TENANCY"],
    availability_domain=e["OCI_AD"],
    display_name=NAME,
    shape="VM.Standard.A1.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=2, memory_in_gbs=12),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id=e["OCI_IMAGE"], boot_volume_size_in_gbs=50),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id=e["OCI_SUBNET"], assign_public_ip=True),
    metadata={"ssh_authorized_keys": e["SSH_PUBKEY"]},
)

try:
    compute.launch_instance(details)
except oci.exceptions.ServiceError as err:
    if err.status in (500, 429) or "capacity" in str(err.message).lower():
        print("No capacity yet.")
        sys.exit(0)
    print(f"Unexpected error: HTTP {err.status} {err.code}")
    sys.exit(1)

print("Server created.")
done()
