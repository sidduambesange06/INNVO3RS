import type { Drone, Incident, Camera, SosRequest, HeatZone, AlertEvent } from '../types';

export const drones: Drone[] = [
  {
    id: 'SKY-01', status: 'EN_ROUTE', battery: 78, speed: 42,
    lat: 18.5280, lng: 73.8500, // En route to INC-001 (approx)
    destLat: 18.5320, destLng: 73.8478, destination: 'INC-001', incidentId: 'INC-001',
    eta: 272, score: 92, trail: [[18.5200, 73.8500], [18.5220, 73.8500], [18.5240, 73.8500], [18.5260, 73.8500]]
  },
  {
    id: 'SKY-02', status: 'AVAILABLE', battery: 95, speed: 0,
    lat: 18.5260, lng: 73.8650, // Near SOS-002
    destLat: null, destLng: null, destination: null, incidentId: null,
    eta: null, score: 98, trail: [[18.5260, 73.8650]]
  },
  {
    id: 'SKY-03', status: 'DISPATCHED', battery: 61, speed: 38,
    lat: 18.5204, lng: 73.8567, // Center
    destLat: 18.5150, destLng: 73.8620, destination: 'INC-002', incidentId: 'INC-002',
    eta: 340, score: 75, trail: [[18.5204, 73.8567]]
  },
  {
    id: 'SKY-04', status: 'CHARGING', battery: 22, speed: 0,
    lat: 18.5300, lng: 73.8400,
    destLat: null, destLng: null, destination: null, incidentId: null,
    eta: null, score: 100, trail: [[18.5300, 73.8400]]
  },
  {
    id: 'SKY-05', status: 'REROUTING', battery: 55, speed: 35,
    lat: 18.5180, lng: 73.8500,
    destLat: 18.5320, destLng: 73.8478, destination: 'INC-001', incidentId: 'INC-001', // Example reroute
    eta: 180, score: 60, trail: [[18.5140, 73.8520], [18.5160, 73.8510], [18.5180, 73.8500]]
  },
  {
    id: 'SKY-06', status: 'RETURNING', battery: 43, speed: 28,
    lat: 18.5100, lng: 73.8600,
    destLat: 18.5300, destLng: 73.8400, destination: 'Base', incidentId: null,
    eta: 450, score: 80, trail: [[18.5080, 73.8620], [18.5100, 73.8600]]
  }
];

export const incidents: Incident[] = [
  {
    id: 'INC-001', lat: 18.5320, lng: 73.8478, severity: 'CRITICAL',
    type: 'Crowd Surge', cameraId: 'CAM-A', assignedDrone: 'SKY-01', timestamp: new Date(Date.now() - 600000)
  },
  {
    id: 'INC-002', lat: 18.5150, lng: 73.8620, severity: 'HIGH',
    type: 'Traffic Accident', cameraId: 'CAM-C', assignedDrone: 'SKY-03', timestamp: new Date(Date.now() - 300000)
  },
  {
    id: 'INC-003', lat: 18.5250, lng: 73.8700, severity: 'MEDIUM',
    type: 'Suspicious Activity', cameraId: 'CAM-B', assignedDrone: null, timestamp: new Date(Date.now() - 150000)
  },
  {
    id: 'INC-004', lat: 18.5080, lng: 73.8510, severity: 'LOW',
    type: 'Street Anomaly', cameraId: 'CAM-E', assignedDrone: null, timestamp: new Date(Date.now() - 50000)
  }
];

export const cameras: Camera[] = [
  {
    id: 'CAM-A', name: 'Shivajinagar Crossing', location: '18.5320, 73.8478', status: 'INCIDENT',
    incident: 'INC-001', assignedDrone: 'SKY-01', eta: 272, lastActivity: new Date(),
    boundingBox: true, boundingBoxLabel: 'CROWD SURGE'
  },
  {
    id: 'CAM-B', name: 'FC Road Junction', location: '18.5250, 73.8700', status: 'ANOMALY',
    incident: 'INC-003', assignedDrone: null, eta: null, lastActivity: new Date(),
    boundingBox: true, boundingBoxLabel: 'SUSPICIOUS ACTIVITY'
  },
  {
    id: 'CAM-C', name: 'Pune Station East', location: '18.5150, 73.8620', status: 'INCIDENT',
    incident: 'INC-002', assignedDrone: 'SKY-03', eta: 340, lastActivity: new Date(),
    boundingBox: true, boundingBoxLabel: 'TRAFFIC ACCIDENT'
  },
  {
    id: 'CAM-D', name: 'Koregaon Park Gate', location: '18.5362, 73.8938', status: 'NORMAL',
    incident: null, assignedDrone: null, eta: null, lastActivity: new Date(),
    boundingBox: false, boundingBoxLabel: null
  },
  {
    id: 'CAM-E', name: 'Camp District Main', location: '18.5080, 73.8510', status: 'ANOMALY',
    incident: 'INC-004', assignedDrone: null, eta: null, lastActivity: new Date(),
    boundingBox: true, boundingBoxLabel: 'STREET ANOMALY'
  }
];

export const sosRequests: SosRequest[] = [
  {
    id: 'SOS-001', lat: 18.5180, lng: 73.8580, locationLabel: 'Baner Road', priority: 'HIGH',
    status: 'PENDING', assignedDrone: null, eta: null, timestamp: new Date()
  },
  {
    id: 'SOS-002', lat: 18.5260, lng: 73.8650, locationLabel: 'Aundh', priority: 'MEDIUM',
    status: 'DRONE_ASSIGNED', assignedDrone: 'SKY-02', eta: 120, timestamp: new Date(Date.now() - 300000)
  },
  {
    id: 'SOS-003', lat: 18.5100, lng: 73.8490, locationLabel: 'Kothrud', priority: 'LOW',
    status: 'RESOLVED', assignedDrone: null, eta: null, timestamp: new Date(Date.now() - 3600000)
  }
];

export const heatZones: HeatZone[] = [
  { id: 'HZ-1', name: 'Koregaon Park', riskScore: 88, incidentsToday: 4, avgAnomaly: 0.8, suggestedDrone: 'SKY-05', lat: 18.5362, lng: 73.8938, radius: 800 },
  { id: 'HZ-2', name: 'Shivajinagar Hub', riskScore: 72, incidentsToday: 3, avgAnomaly: 0.6, suggestedDrone: 'SKY-01', lat: 18.5304, lng: 73.8473, radius: 600 },
  { id: 'HZ-3', name: 'Camp District', riskScore: 65, incidentsToday: 2, avgAnomaly: 0.5, suggestedDrone: 'SKY-04', lat: 18.5074, lng: 73.8758, radius: 700 },
  { id: 'HZ-4', name: 'Aundh Corridor', riskScore: 41, incidentsToday: 1, avgAnomaly: 0.3, suggestedDrone: 'SKY-02', lat: 18.5590, lng: 73.8074, radius: 900 },
  { id: 'HZ-5', name: 'Hadapsar Zone', riskScore: 30, incidentsToday: 0, avgAnomaly: 0.1, suggestedDrone: 'SKY-06', lat: 18.5018, lng: 73.9262, radius: 1000 }
];

export const alerts: AlertEvent[] = [
  { id: 'EVT-10', type: 'DRONE DISPATCHED', description: 'SKY-01 dispatched to INC-001 (Crowd Surge)', severity: 'CRITICAL', source: 'SYSTEM', timestamp: new Date(Date.now() - 600000) },
  { id: 'EVT-09', type: 'INCIDENT DETECTED', description: 'Crowd Surge detected at Shivajinagar', severity: 'CRITICAL', source: 'CAM-A', timestamp: new Date(Date.now() - 605000) },
  { id: 'EVT-08', type: 'DRONE DISPATCHED', description: 'SKY-03 dispatched to INC-002 (Traffic Accident)', severity: 'HIGH', source: 'SYSTEM', timestamp: new Date(Date.now() - 300000) },
  { id: 'EVT-07', type: 'INCIDENT DETECTED', description: 'Traffic Accident reported at Pune Station East', severity: 'HIGH', source: 'CAM-C', timestamp: new Date(Date.now() - 305000) },
  { id: 'EVT-06', type: 'ANOMALY DETECTED', description: 'Suspicious Activity at FC Road Junction', severity: 'MEDIUM', source: 'CAM-B', timestamp: new Date(Date.now() - 150000) },
  { id: 'EVT-05', type: 'SOS RECEIVED', description: 'Emergency request from Aundh', severity: 'MEDIUM', source: 'CIVILIAN', timestamp: new Date(Date.now() - 300000) },
  { id: 'EVT-04', type: 'SYSTEM STATUS', description: 'SKY-04 initiated charging protocol', severity: 'LOW', source: 'SKY-04', timestamp: new Date(Date.now() - 2000000) },
  { id: 'EVT-03', type: 'SOS RESOLVED', description: 'Emergency at Kothrud marked resolved', severity: 'LOW', source: 'OPERATOR', timestamp: new Date(Date.now() - 3600000) },
  { id: 'EVT-02', type: 'ANOMALY DETECTED', description: 'Street Anomaly in Camp District', severity: 'LOW', source: 'CAM-E', timestamp: new Date(Date.now() - 50000) },
  { id: 'EVT-01', type: 'DRONE REROUTING', description: 'SKY-05 rerouting based on AI recommendation', severity: 'MEDIUM', source: 'SYSTEM', timestamp: new Date(Date.now() - 120000) }
];

export const initialMockData = { drones, incidents, cameras, sosRequests, heatZones, alerts };
