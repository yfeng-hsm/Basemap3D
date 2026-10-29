from pathlib import Path
import json,numpy as np,rasterio
from rasterio.features import rasterize,shapes
from rasterio.warp import transform_geom
from scipy import ndimage as ndi
from skimage.morphology import remove_small_objects,remove_small_holes,binary_closing,disk
from skimage.feature import peak_local_max
from skimage.segmentation import watershed,find_boundaries
from pyproj import Transformer
from PIL import Image
p=Path(__file__).parent;out=p/'output';out.mkdir(exist_ok=True)
with rasterio.open(p/'dom1_mosaic.tif') as d:dom=d.read(1);profile=d.profile.copy();tr=d.transform
with rasterio.open(p/'dgm1_mosaic.tif') as d:ground=d.read(1)
with rasterio.open(p/'rgbi_1m_mosaic.tif') as d:rgbi=d.read()
valid=(dom!=-9999)&(ground!=-9999)&np.isfinite(dom)&np.isfinite(ground)
chm=np.where(valid,np.maximum(dom-ground,0),0)
ndvi=(rgbi[3].astype('float32')-rgbi[0])/(rgbi[3].astype('float32')+rgbi[0]+1e-5)
city=json.loads((p/'mainz-boundary.json').read_text())[0]['geojson']
city_utm=transform_geom('EPSG:4326','EPSG:25832',city)
citymask=rasterize([(city_utm,1)],out_shape=chm.shape,transform=tr,dtype='uint8').astype(bool)
buildings=json.loads((p/'building_footprints.geojson').read_text())['features']
bg=[(transform_geom('EPSG:4326','EPSG:25832',f['geometry']),1) for f in buildings]
bmask=rasterize(bg,out_shape=chm.shape,transform=tr,dtype='uint8').astype(bool)

mask=valid&citymask&(~bmask)&(ndvi>.25)&(chm>2.5)&(chm<45)
mask=binary_closing(mask,footprint=disk(1))&valid&citymask&(~bmask)&(chm>2.0)
mask=remove_small_holes(mask,area_threshold=12);mask=remove_small_objects(mask,min_size=8)
# Preserve the footprint exclusion after hole filling.
mask&=~bmask
smooth=ndi.gaussian_filter(np.minimum(chm,40),0.6)
components,nc=ndi.label(mask);peaks=peak_local_max(smooth,min_distance=2,threshold_abs=3,labels=components,exclude_border=False)
markers=np.zeros(chm.shape,'int32')
for i,(r,c) in enumerate(peaks,1):markers[r,c]=i
next_id=len(peaks)
for cid,sl in enumerate(ndi.find_objects(components),1):
 if sl is None:continue
 region=components[sl]==cid
 if not np.any(markers[sl][region]):
  scores=np.where(region,smooth[sl],-np.inf);r,c=np.unravel_index(scores.argmax(),scores.shape);next_id+=1;markers[sl][r,c]=next_id
labels=watershed(-smooth,markers,mask=mask);accepted=np.zeros(labels.shape,'int32');features=[];attributes=[]
towgs=Transformer.from_crs(25832,4326,always_xy=True)
for lab,sl in enumerate(ndi.find_objects(labels),1):
 if sl is None:continue
 rr,cc=np.where(labels[sl]==lab);rr+=sl[0].start;cc+=sl[1].start
 if len(rr)<8:continue
 height=float(np.percentile(chm[rr,cc],99))
 if not 3<=height<=40:continue
 k=np.argmax(smooth[rr,cc]);pr,pc=int(rr[k]),int(cc[k]);e=446000+pc+.5;n=5540000-pr-.5;lon,lat=towgs.transform(e,n);tid=f'mainz_center_{len(features)+1:06d}'
 row={'tree_id':tid,'easting':e,'northing':n,'longitude':round(lon,8),'latitude':round(lat,8),'ground_height_dgm1_m':round(float(ground[pr,pc]),3),'height_m':round(height,2),'crown_area_m2':len(rr),'crown_diameter_equivalent_m':round(2*np.sqrt(len(rr)/np.pi),2),'mean_ndvi':round(float(ndvi[rr,cc].mean()),3),'tile':f'32_{int(e//1000)}_{int(n//1000)}','edge_truncated':bool(np.any((rr==0)|(rr==2999)|(cc==0)|(cc==2999))),'review_recommended':bool(height>30),'height_method':'P99(pixelwise DOM1-DGM1)'}
 attributes.append(row);features.append({'type':'Feature','id':tid,'geometry':{'type':'Point','coordinates':[round(lon,8),round(lat,8)]},'properties':row});accepted[rr,cc]=len(features)
(out/'tree_points.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')))
(out/'tree_attributes.json').write_text(json.dumps(attributes,separators=(',',':')))
profile.update(count=1,dtype='int32',nodata=0,compress='deflate')
with rasterio.open(p/'crown_labels_center.tif','w',**profile) as d:d.write(accepted,1)
profile.update(dtype='float32',nodata=-9999)
with rasterio.open(p/'chm_center.tif','w',**profile) as d:d.write(np.where(valid,chm,-9999).astype('float32'),1)
# Diagnostic overview: footprints red, candidate crown boundaries yellow.
rgb=rgbi[:3].transpose(1,2,0);overlay=rgb.copy();edge=find_boundaries(accepted,mode='outer');overlay[edge]=[255,210,45]
Image.fromarray(overlay).resize((1500,1500)).save(out/'crown_overlay_center.jpg',quality=90)
counts={}
for row in attributes:counts[row['tile']]=counts.get(row['tile'],0)+1
stats={'selected_frame_area_km2':9,'mainz_area_inside_frame_km2':round(np.count_nonzero(citymask)/1e6,3),'candidate_tree_count':len(features),'height_range_m':[min(x['height_m'] for x in attributes),max(x['height_m'] for x in attributes)],'height_over_30m_review_count':sum(x['review_recommended'] for x in attributes),'building_footprints_used':len(buildings),'tile_counts':counts,'method':{'ndvi_min':.25,'minimum_height_m':3,'minimum_crown_area_m2':8,'peak_spacing_m':2,'building_exclusion_buffer_m_approx':0,'configuration':'C_balanced','mask_min_height_m':2.5,'smoothed_sigma_m':0.6,'height_estimation':'P99(pixelwise DOM1-DGM1)','municipal_mask':'OpenStreetMap Mainz relation 62630'},'limits':['Automatic candidates; not field-verified.','Closely spaced trees may merge or split.','OSM building omissions and crown overhangs can cause errors or omissions.','2023 elevation and 2024 imagery are not simultaneous.']}
(out/'processing_summary.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2),flush=True)
