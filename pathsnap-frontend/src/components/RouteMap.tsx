import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Maximize2, Map, Code, Layers } from 'lucide-react';
import { LatLngCoord, GPSObservation } from '../types/api';
import { computeBoundingBox, calculateRouteLengthKm } from '../utils/coordinates';

interface RouteMapProps {
  gpsCoordinates: GPSObservation[];
  predictedRouteCoordinates: LatLngCoord[];
  roadNetworkCoordinates?: LatLngCoord[][];
  foliumHtml?: string | null;
  tripId: string | null;
}

export const RouteMap: React.FC<RouteMapProps> = ({
  gpsCoordinates,
  predictedRouteCoordinates,
  roadNetworkCoordinates = [],
  foliumHtml,
  tripId,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  // Layer groups
  const gpsLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const routeLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const roadNetworkLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const markersLayerGroupRef = useRef<L.LayerGroup | null>(null);

  // Layer visibility state
  const [showGps, setShowGps] = useState(true);
  const [showPredictedRoute, setShowPredictedRoute] = useState(true);
  const [showRoadNetwork, setShowRoadNetwork] = useState(true);

  // Tab mode: 'leaflet' or 'folium'
  const [activeTab, setActiveTab] = useState<'leaflet' | 'folium'>('leaflet');

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [54.96, 56.25],
        zoom: 13,
        zoomControl: true,
      });

      // CartoDB Dark Matter / Positron or OpenStreetMap
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 19,
      }).addTo(map);

      gpsLayerGroupRef.current = L.layerGroup().addTo(map);
      routeLayerGroupRef.current = L.layerGroup().addTo(map);
      roadNetworkLayerGroupRef.current = L.layerGroup().addTo(map);
      markersLayerGroupRef.current = L.layerGroup().addTo(map);

      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Sync layer visibility
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (gpsLayerGroupRef.current) {
      if (showGps && !map.hasLayer(gpsLayerGroupRef.current)) {
        map.addLayer(gpsLayerGroupRef.current);
      } else if (!showGps && map.hasLayer(gpsLayerGroupRef.current)) {
        map.removeLayer(gpsLayerGroupRef.current);
      }
    }

    if (routeLayerGroupRef.current) {
      if (showPredictedRoute && !map.hasLayer(routeLayerGroupRef.current)) {
        map.addLayer(routeLayerGroupRef.current);
      } else if (!showPredictedRoute && map.hasLayer(routeLayerGroupRef.current)) {
        map.removeLayer(routeLayerGroupRef.current);
      }
    }

    if (roadNetworkLayerGroupRef.current) {
      if (showRoadNetwork && !map.hasLayer(roadNetworkLayerGroupRef.current)) {
        map.addLayer(roadNetworkLayerGroupRef.current);
      } else if (!showRoadNetwork && map.hasLayer(roadNetworkLayerGroupRef.current)) {
        map.removeLayer(roadNetworkLayerGroupRef.current);
      }
    }
  }, [showGps, showPredictedRoute, showRoadNetwork]);

  // Update map contents whenever coordinates change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear existing layers
    gpsLayerGroupRef.current?.clearLayers();
    routeLayerGroupRef.current?.clearLayers();
    roadNetworkLayerGroupRef.current?.clearLayers();
    markersLayerGroupRef.current?.clearLayers();

    const allPointsForBounds: LatLngCoord[] = [];

    // 1. Draw Road Network (if available, gray lines)
    if (roadNetworkCoordinates.length > 0 && roadNetworkLayerGroupRef.current) {
      roadNetworkCoordinates.forEach((seg) => {
        if (seg.length >= 2) {
          L.polyline(seg, {
            color: '#64748b',
            weight: 2,
            opacity: 0.6,
          }).addTo(roadNetworkLayerGroupRef.current!);
        }
      });
    }

    // 2. Draw GPS Observation Markers (Blue dots)
    if (gpsCoordinates.length > 0 && gpsLayerGroupRef.current) {
      gpsCoordinates.forEach((obs, idx) => {
        const lat = obs[0];
        const lng = obs[1];
        const ts = obs[2];
        allPointsForBounds.push([lat, lng]);

        const marker = L.circleMarker([lat, lng], {
          radius: 4,
          fillColor: '#3b82f6',
          color: '#1d4ed8',
          weight: 1,
          opacity: 0.9,
          fillOpacity: 0.7,
        });

        marker.bindTooltip(
          `<strong>GPS Point #${idx + 1}</strong><br/>Lat: ${lat.toFixed(5)}<br/>Lon: ${lng.toFixed(5)}${ts ? `<br/>Time: ${ts}` : ''}`,
          { direction: 'top' }
        );

        marker.addTo(gpsLayerGroupRef.current!);
      });
    }

    // 3. Draw Predicted Route Polyline (Vibrant Red/Purple)
    if (predictedRouteCoordinates.length > 0 && routeLayerGroupRef.current) {
      predictedRouteCoordinates.forEach((pt) => allPointsForBounds.push(pt));

      const polyline = L.polyline(predictedRouteCoordinates, {
        color: '#e11d48', // High-contrast Red/Rose
        weight: 5,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round',
      });

      polyline.bindPopup(
        `<strong>PathSnap Decoded Trajectory</strong><br/>Segments: ${predictedRouteCoordinates.length} nodes<br/>Est. Distance: ${calculateRouteLengthKm(predictedRouteCoordinates).toFixed(2)} km`
      );

      polyline.addTo(routeLayerGroupRef.current!);

      // Start and Finish Markers
      if (markersLayerGroupRef.current && predictedRouteCoordinates.length >= 2) {
        const startPoint = predictedRouteCoordinates[0];
        const endPoint = predictedRouteCoordinates[predictedRouteCoordinates.length - 1];

        // Start Icon
        const startIcon = L.divIcon({
          className: 'custom-start-marker',
          html: `<div style="background-color: #10b981; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.4);">S</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        // End Icon
        const endIcon = L.divIcon({
          className: 'custom-end-marker',
          html: `<div style="background-color: #e11d48; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.4);">E</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        L.marker(startPoint, { icon: startIcon }).bindTooltip('Trip Start').addTo(markersLayerGroupRef.current);
        L.marker(endPoint, { icon: endIcon }).bindTooltip('Trip Destination').addTo(markersLayerGroupRef.current);
      }
    }

    // Auto-fit bounds
    if (allPointsForBounds.length > 0) {
      const bbox = computeBoundingBox(allPointsForBounds);
      if (bbox) {
        map.fitBounds(bbox, { padding: [40, 40], maxZoom: 16 });
      }
    }

    // Trigger map invalidation for container resizing
    setTimeout(() => {
      map.invalidateSize();
    }, 100);
  }, [gpsCoordinates, predictedRouteCoordinates, roadNetworkCoordinates]);

  const fitCurrentBounds = () => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const points: LatLngCoord[] = [
      ...predictedRouteCoordinates,
      ...gpsCoordinates.map((c) => [c[0], c[1]] as LatLngCoord),
    ];
    const bbox = computeBoundingBox(points);
    if (bbox) {
      map.fitBounds(bbox, { padding: [40, 40], maxZoom: 16 });
    }
  };

  const hasData = gpsCoordinates.length > 0 || predictedRouteCoordinates.length > 0;

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-sm overflow-hidden flex flex-col h-[560px]">
      {/* Top Map Toolbar */}
      <div className="bg-slate-900/80 px-4 py-2.5 border-b border-slate-700/80 flex flex-wrap items-center justify-between gap-2 z-10">
        <div className="flex items-center space-x-2">
          {/* View Tab Buttons */}
          <div className="bg-slate-800 p-0.5 rounded-lg border border-slate-700 flex items-center">
            <button
              onClick={() => setActiveTab('leaflet')}
              className={`px-3 py-1 rounded-md text-xs font-medium flex items-center space-x-1.5 transition-colors ${
                activeTab === 'leaflet'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Map className="h-3.5 w-3.5" />
              <span>Interactive Leaflet</span>
            </button>
            <button
              onClick={() => setActiveTab('folium')}
              className={`px-3 py-1 rounded-md text-xs font-medium flex items-center space-x-1.5 transition-colors ${
                activeTab === 'folium'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="h-3.5 w-3.5" />
              <span>Folium Map View</span>
            </button>
          </div>

          {tripId && (
            <span className="text-xs text-slate-400 hidden sm:inline">
              Viewing: <strong className="text-slate-200 font-mono">{tripId}</strong>
            </span>
          )}
        </div>

        {/* Layer Controls & Actions (only for Leaflet view) */}
        {activeTab === 'leaflet' && (
          <div className="flex items-center space-x-3 text-xs">
            <div className="flex items-center space-x-2 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700">
              <Layers className="h-3.5 w-3.5 text-slate-400 mr-0.5" />

              {/* GPS Points Toggle */}
              <label className="flex items-center space-x-1 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={showGps}
                  onChange={(e) => setShowGps(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-600 text-blue-500 focus:ring-0 text-xs"
                />
                <span className="flex items-center text-blue-400 font-medium">
                  <span className="h-2 w-2 rounded-full bg-blue-500 mr-1"></span>
                  GPS ({gpsCoordinates.length})
                </span>
              </label>

              <span className="text-slate-600">|</span>

              {/* Predicted Route Toggle */}
              <label className="flex items-center space-x-1 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={showPredictedRoute}
                  onChange={(e) => setShowPredictedRoute(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-600 text-rose-500 focus:ring-0 text-xs"
                />
                <span className="flex items-center text-rose-400 font-medium">
                  <span className="h-2 w-2 rounded-full bg-rose-500 mr-1"></span>
                  Predicted Route
                </span>
              </label>

              {roadNetworkCoordinates.length > 0 && (
                <>
                  <span className="text-slate-600">|</span>
                  <label className="flex items-center space-x-1 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={showRoadNetwork}
                      onChange={(e) => setShowRoadNetwork(e.target.checked)}
                      className="rounded bg-slate-900 border-slate-600 text-slate-400 focus:ring-0 text-xs"
                    />
                    <span className="text-slate-400">Roads</span>
                  </label>
                </>
              )}
            </div>

            {hasData && (
              <button
                onClick={fitCurrentBounds}
                className="p-1.5 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
                title="Fit to Route Bounds"
              >
                <Maximize2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Map View Container */}
      <div className="relative flex-1 bg-slate-950">
        {/* Leaflet Map Div */}
        <div
          ref={mapContainerRef}
          className={`w-full h-full ${activeTab === 'leaflet' ? 'block' : 'hidden'}`}
        />

        {/* Folium HTML Iframe View */}
        {activeTab === 'folium' && (
          <div className="w-full h-full flex flex-col">
            {foliumHtml ? (
              <iframe
                title="Folium Backend Map"
                srcDoc={foliumHtml}
                className="w-full h-full border-none bg-white"
                sandbox="allow-scripts allow-same-origin"
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center p-6 text-slate-400">
                <Code className="h-10 w-10 text-slate-600 mb-3" />
                <h4 className="text-sm font-semibold text-slate-300">Folium HTML Not Provided</h4>
                <p className="text-xs max-w-sm mt-1">
                  Laptop 1 backend did not include a pre-rendered Folium HTML string for this trip. The interactive Leaflet viewer is active and fully functional.
                </p>
                <button
                  onClick={() => setActiveTab('leaflet')}
                  className="mt-4 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium"
                >
                  Return to Leaflet View
                </button>
              </div>
            )}
          </div>
        )}

        {/* Empty State Overlay */}
        {!hasData && (
          <div className="absolute inset-0 bg-slate-900/70 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center pointer-events-none">
            <div className="h-12 w-12 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mb-3 text-slate-500">
              <Map className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Awaiting Prediction</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              Select one of the 10 evaluation trips from the dropdown above and click &ldquo;Run Prediction&rdquo; to visualize the reconstructed route.
            </p>
          </div>
        )}

        {/* Floating Map Legend (Bottom Left) */}
        {activeTab === 'leaflet' && hasData && (
          <div className="absolute bottom-4 left-4 z-[400] bg-slate-900/90 backdrop-blur-md p-3 rounded-xl border border-slate-700/80 shadow-lg text-[11px] space-y-1.5">
            <div className="font-semibold text-slate-200 border-b border-slate-700/60 pb-1 mb-1">
              Route Legend
            </div>
            <div className="flex items-center space-x-2">
              <span className="h-2.5 w-2.5 rounded-full bg-blue-500 ring-2 ring-blue-700"></span>
              <span className="text-slate-300">Raw GPS Observations</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="h-1.5 w-4 rounded-full bg-rose-500"></span>
              <span className="text-slate-300">HMM-Decoded Route</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="h-4 w-4 rounded-full bg-emerald-500 text-white text-[9px] font-bold flex items-center justify-center">S</span>
              <span className="text-slate-300">Start Point</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="h-4 w-4 rounded-full bg-rose-600 text-white text-[9px] font-bold flex items-center justify-center">E</span>
              <span className="text-slate-300">Destination Point</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

