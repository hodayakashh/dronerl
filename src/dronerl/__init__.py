"""DroneRL — Smart City Drone Delivery via Q-Learning (BIU Deep RL Course).

Public API is exposed through DroneRLSDK — the single entry point for all
business logic. External consumers should import only from this module.
"""

from dronerl.sdk import DroneRLSDK
from dronerl.shared.version import VERSION

__version__ = VERSION
__all__ = ["__version__", "DroneRLSDK"]
