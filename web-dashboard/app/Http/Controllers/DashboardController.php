<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

use App\Models\IncidentLog;

class DashboardController extends Controller
{
    private function getConfigPath()
    {
        return base_path('../config.json');
    }

    public function index()
    {
        $config = [];
        if (file_exists($this->getConfigPath())) {
            $config = json_decode(file_get_contents($this->getConfigPath()), true);
        }
        $logs = IncidentLog::latest()->take(20)->get();
        $totalIncidents = IncidentLog::count();
        $activeZonesCount = isset($config['chair_zones']) ? count($config['chair_zones']) : 0;

        return view('dashboard', compact('config', 'logs', 'totalIncidents', 'activeZonesCount'));
    }

    public function getLogs()
    {
        return response()->json([
            'logs' => IncidentLog::latest()->take(50)->get(),
            'total' => IncidentLog::count()
        ]);
    }

    public function getConfig()
    {
        if (file_exists($this->getConfigPath())) {
            return response()->json(json_decode(file_get_contents($this->getConfigPath()), true));
        }
        return response()->json(['error' => 'Config file not found'], 404);
    }

    public function updateConfig(Request $request)
    {
        $validated = $request->validate([
            'source' => 'required|string',
            'confidence' => 'required|numeric',
            'enter_seconds' => 'required|numeric',
            'exit_seconds' => 'required|numeric',
            'miss_tolerance_seconds' => 'required|numeric',
            'stream_url' => 'nullable|string',
        ]);

        $currentConfig = [];
        if (file_exists($this->getConfigPath())) {
            $currentConfig = json_decode(file_get_contents($this->getConfigPath()), true);
        }

        $mergedConfig = array_merge($currentConfig, $validated);

        if ($request->has('chair_zones')) {
            $mergedConfig['chair_zones'] = $request->input('chair_zones');
        }

        file_put_contents($this->getConfigPath(), json_encode($mergedConfig, JSON_PRETTY_PRINT));

        return response()->json(['status' => 'success', 'config' => $mergedConfig]);
    }

    public function storeIncident(Request $request)
    {
        $validated = $request->validate([
            'zone_id' => 'required|string',
            'event_type' => 'required|string',
            'person_count' => 'nullable|integer',
            'duration_seconds' => 'nullable|numeric',
            'description' => 'nullable|string',
        ]);

        $log = IncidentLog::create([
            'zone_id' => $validated['zone_id'],
            'event_type' => $validated['event_type'],
            'person_count' => $validated['person_count'] ?? 1,
            'duration_seconds' => $validated['duration_seconds'] ?? null,
            'description' => $validated['description'] ?? 'Event detected',
        ]);

        return response()->json(['status' => 'success', 'log' => $log]);
    }
}
