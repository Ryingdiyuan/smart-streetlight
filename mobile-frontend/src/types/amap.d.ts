declare interface AMapLngLat {
  lat: number;
  lng: number;
}

declare interface AMapMarker {
  setMap(map: AMapMap | null): void;
  on(event: string, handler: () => void): void;
}

declare interface AMapMap {
  setFitView(markers?: AMapMarker[], immediately?: boolean, padding?: [number, number, number, number]): void;
  destroy(): void;
}

declare interface Window {
  AMap: {
    Map: new (
      container: HTMLDivElement,
      options: { zoom: number; center: [number, number]; mapStyle?: string; resizeEnable?: boolean },
    ) => AMapMap;
    Marker: new (options: { position: [number, number]; title?: string }) => AMapMarker;
  };
}
