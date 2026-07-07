/* 高德地图 AMap 类型声明 */

declare global {
  interface AMapLngLat {
    lng: number;
    lat: number;
  }

  interface AMapMap {
    destroy: () => void;
    setCenter: (center: [number, number]) => void;
    setZoom: (zoom: number) => void;
    add: (layer: unknown) => void;
    remove: (layer: unknown) => void;
    setFitView: (overlayList?: unknown[], immediate?: boolean, avoid?: number[], maxZoom?: number) => void;
    on: (event: string, handler: (e: { lnglat: AMapLngLat }) => void) => void;
    off: (event: string, handler: (e: { lnglat: AMapLngLat }) => void) => void;
    getCenter: () => AMapLngLat;
    pixelToLngLat: (x: number, y: number) => AMapLngLat;
  }

  interface AMapMarker {
    setPosition: (pos: [number, number]) => void;
    setMap: (map: AMapMap | null) => void;
    on: (event: string, handler: (e?: { lnglat: AMapLngLat; _stopPropagation?: boolean }) => void) => void;
    getPosition: () => AMapLngLat;
    setContent: (content: string | HTMLElement) => void;
    setDraggable: (draggable: boolean) => void;
  }

  interface AMapInfoWindow {
    open: (map: AMapMap, pos: AMapLngLat) => void;
    setContent: (content: string) => void;
    close: () => void;
  }

  interface Window {
    AMap: {
      Map: new (container: string | HTMLElement, opts?: Record<string, unknown>) => AMapMap;
      Marker: new (opts?: Record<string, unknown>) => AMapMarker;
      InfoWindow: new (opts?: Record<string, unknown>) => AMapInfoWindow;
      plugin: (plugins: string[], callback: () => void) => void;
      LngLat: new (lng: number, lat: number) => AMapLngLat;
      Pixel: new (x: number, y: number) => { x: number; y: number };
    };
  }
}

export {};
