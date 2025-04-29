# Jersey Weather Integration in Home Assistant UI

Once installed, the Jersey Weather integration will add several entities to your Home Assistant instance. Here's an example of how you might configure these in your Home Assistant UI:

## Main Weather Card

You can add the Jersey Weather entity to your dashboard as a weather card:

```yaml
type: weather-forecast
entity: weather.jersey_weather
```

## Current Weather Stats Card

You can create a glance card with the current weather conditions:

```yaml
type: glance
entities:
  - entity: sensor.current_temperature
  - entity: sensor.wind_speed
  - entity: sensor.uv_index
  - entity: sensor.sunrise
  - entity: sensor.sunset
title: Jersey Weather Statistics
```

## Tide Information

You can create a entities card with the tide information:

```yaml
type: entities
entities:
  - entity: sensor.tide_1
  - entity: sensor.tide_2
  - entity: sensor.tide_3
  - entity: sensor.tide_4
title: Jersey Tides
```

## Weather Images

You can create a picture-glance card for each weather image:

```yaml
type: picture-entity
entity: camera.jersey_weather_radar
title: Jersey Radar
camera_view: auto
```

```yaml
type: picture-entity
entity: camera.jersey_weather_satellite
title: Jersey Satellite
camera_view: auto
```

## Full Dashboard Example

For a complete weather dashboard, you might use a grid layout like this:

```yaml
type: grid
cards:
  - type: weather-forecast
    entity: weather.jersey_weather
    name: Jersey Weather
    forecast_type: daily
  
  - type: glance
    entities:
      - entity: sensor.current_temperature
      - entity: sensor.wind_speed
      - entity: sensor.wind_direction
      - entity: sensor.uv_index
    title: Current Conditions
  
  - type: entities
    entities:
      - entity: sensor.tide_1
      - entity: sensor.tide_2
      - entity: sensor.tide_3
      - entity: sensor.tide_4
    title: Today's Tides
  
  - type: grid
    cards:
      - type: picture-entity
        entity: camera.jersey_weather_radar
        title: Radar
        camera_view: auto
      
      - type: picture-entity
        entity: camera.jersey_weather_satellite
        title: Satellite
        camera_view: auto
    columns: 2
    square: false
    
  - type: grid
    cards:
      - type: picture-entity
        entity: camera.jersey_weather_sea_state_am
        title: Sea State AM
        camera_view: auto
      
      - type: picture-entity
        entity: camera.jersey_weather_sea_state_pm
        title: Sea State PM
        camera_view: auto
    columns: 2
    square: false
```

## Automation Ideas

Here are some automation ideas using the Jersey Weather integration:

### Close Windows When Rain Expected

```yaml
alias: Close Windows When Rain Expected
description: "Close windows when rain is expected in the next few hours"
trigger:
  - platform: state
    entity_id: sensor.weather_condition
  - platform: numeric_state
    entity_id: sensor.tide_1
    attribute: rain_probability_afternoon
    above: 50
condition:
  - condition: numeric_state
    entity_id: sensor.tide_1
    attribute: rain_probability_afternoon
    above: 50
action:
  - service: cover.close_cover
    target:
      entity_id: cover.living_room_window
```

### UV Warning Notification

```yaml
alias: UV Warning
description: "Send notification when UV index is high"
trigger:
  - platform: numeric_state
    entity_id: sensor.uv_index
    above: 6
condition: []
action:
  - service: notify.mobile_app
    data:
      message: "UV index is high today ({{ states('sensor.uv_index') }}). Don't forget sunscreen!"
```
