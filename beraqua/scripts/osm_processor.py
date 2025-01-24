import osmium as osm
import geopandas as gpd


class OSMHandler(osm.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = []

    def node(self, n):
        self.nodes.append({
            'id': n.id,
            'lon': n.location.lon,
            'lat': n.location.lat,
            'tags': dict(n.tags)
        })


# Initialize handler and read the file
handler = OSMHandler()


handler.apply_file('/home/luisvinatea/Dev/Repos/aquaculture/beraqua/data/raw/maps/guayas.osm')

# Convert nodes to GeoDataFrame
gdf = gpd.GeoDataFrame(
    handler.nodes,
    geometry=gpd.points_from_xy([node['lon'] for node in handler.nodes],
                                [node['lat'] for node in handler.nodes]),
    crs='EPSG:4326'
)


# Save as GeoJSON or Shapefile
gdf.to_file('/home/luisvinatea/Dev/Repos/aquaculture/beraqua/data/processed/maps/guayas.geojson', driver='GeoJSON')
print(gdf.head())
