from ..query import PointCloud


def get_smallest_bounding_box(pc: PointCloud, res: float) -> tuple[float, float, float, float]:
    """
    Calculates the smallest axis-aligned bounding box that contains all points in the given PointCloud, 
    snapping the box edges to the specified resolution. 
    Returns a tuple (lat_min, lat_max, lon_min, lon_max) representing the bounding box boundaries.
    """
    lat_min, lat_max = min(pc.lats), max(pc.lats)
    lon_min, lon_max = min(pc.lons), max(pc.lons)
    
    def snap(val, res, mode="down"):
        if mode == "down":
            return (val // res) * res
        else:
            return ((val + res) // res) * res
    
    return (
        snap(lat_min, res, mode="down"),
        snap(lat_max, res, mode="up"),
        snap(lon_min, res, mode="down"),
        snap(lon_max, res, mode="up"),
    )
