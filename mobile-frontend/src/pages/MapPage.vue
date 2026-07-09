<template>
  <div class="page-stack">
    <SectionCard title="设备地图" subtitle="移动端快速定位在线与离线状态">
      <div ref="mapContainer" class="map-container"></div>
      <p v-if="errorMessage" class="placeholder-text">{{ errorMessage }}</p>
      <div v-if="selectedDevice" class="map-device-card">
        <div>
          <p>{{ selectedDevice.deviceCode }}</p>
          <strong>{{ selectedDevice.deviceName }}</strong>
          <span>{{ selectedDevice.location }}</span>
        </div>
        <button class="action-button" type="button" @click="router.push(`/devices/${selectedDevice.id}`)">查看设备</button>
      </div>
    </SectionCard>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import SectionCard from "@/components/SectionCard.vue";
import { getDeviceList } from "@/services/api/deviceService";
import type { Device } from "@/types/models";

const router = useRouter();
const mapContainer = ref<HTMLDivElement | null>(null);
const selectedDevice = ref<Device | null>(null);
const errorMessage = ref("");

let map: AMapMap | null = null;
let markers: AMapMarker[] = [];

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || "";

function clearMarkers() {
  markers.forEach((marker) => marker.setMap(null));
  markers = [];
}

async function loadAmap() {
  if (window.AMap) {
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("高德地图加载失败"));
    document.head.appendChild(script);
  });
}

async function renderMap() {
  if (!mapContainer.value) {
    return;
  }

  if (!AMAP_KEY) {
    errorMessage.value = "未配置高德地图 Key。";
    return;
  }

  try {
    await loadAmap();
    const devices = await getDeviceList();

    map = new window.AMap.Map(mapContainer.value, {
      zoom: 15,
      center: [106.528, 29.531],
      mapStyle: "amap://styles/darkblue",
      resizeEnable: true,
    });

    const pointDevices = devices.filter((device) => device.latitude !== undefined && device.longitude !== undefined);
    markers = pointDevices.map((device) => {
      const marker = new window.AMap.Marker({
        position: [device.longitude!, device.latitude!],
        title: device.deviceName,
      });
      marker.setMap(map!);
      marker.on("click", () => {
        selectedDevice.value = device;
      });
      return marker;
    });

    if (markers.length) {
      map.setFitView(markers, false, [24, 24, 24, 24]);
      selectedDevice.value = pointDevices[0] ?? null;
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "地图加载失败";
  }
}

onMounted(renderMap);

onUnmounted(() => {
  clearMarkers();
  if (map) {
    map.destroy();
    map = null;
  }
});
</script>

<style scoped>
.map-container {
  height: 420px;
  border-radius: 22px;
  overflow: hidden;
}

.map-device-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: var(--surface-subtle);
  border: 1px solid var(--border-soft);
}

.map-device-card p,
.map-device-card strong,
.map-device-card span {
  margin: 0;
}

.map-device-card p {
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.map-device-card span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
