<?php

use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
|
| Here is where you can register web routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| contains the "web" middleware group. Now create something great!
|
*/

use App\Http\Controllers\DashboardController;

Route::get('/', [DashboardController::class, 'index']);
Route::get('/logs', [DashboardController::class, 'getLogs']);
Route::get('/config', [DashboardController::class, 'getConfig']);
Route::post('/config', [DashboardController::class, 'updateConfig']);
Route::get('/stream-proxy', [DashboardController::class, 'streamProxy']);
Route::post('/api/incidents', [DashboardController::class, 'storeIncident']);
