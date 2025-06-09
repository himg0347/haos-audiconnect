refresh_vehicle_data:
  name: Refresh vehicle data
  description: Refresh data for a specific vehicle
  fields:
    vin:
      name: VIN
      description: Vehicle Identification Number
      required: true
      selector:
        text:

execute_vehicle_action:
  name: Execute vehicle action
  description: Execute an action on a vehicle
  fields:
    vin:
      name: VIN
      description: Vehicle Identification Number
      required: true
      selector:
        text:
    action:
      name: Action
      description: Action to perform on the vehicle
      required: true
      selector:
        select:
          options:
            - "lock"
            - "unlock"
            - "start_climatisation"
            - "stop_climatisation"
            - "start_charger"
            - "stop_charger"
            - "start_preheater"
            - "stop_preheater"
            - "start_window_heating"
            - "stop_window_heating"

start_climate_control:
  name: Start climate control
  description: Start climate control with specified settings
  fields:
    vin:
      name: VIN
      description: Vehicle Identification Number
      required: true
      selector:
        text:
    temp_f:
      name: Temperature (Fahrenheit)
      description: Target temperature in Fahrenheit
      required: false
      selector:
        number:
          min: 32
          max: 100
          step: 1
    temp_c:
      name: Temperature (Celsius)
      description: Target temperature in Celsius
      required: false
      selector:
        number:
          min: 0
          max: 38
          step: 0.5
    glass_heating:
      name: Glass Heating
      description: Enable glass heating
      required: false
      selector:
        boolean:
    seat_fl:
      name: Front Left Seat
      description: Enable front left seat heating
      required: false
      selector:
        boolean:
    seat_fr:
      name: Front Right Seat
      description: Enable front right seat heating
      required: false
      selector:
        boolean:
    seat_rl:
      name: Rear Left Seat
      description: Enable rear left seat heating
      required: false
      selector:
        boolean:
    seat_rr:
      name: Rear Right Seat
      description: Enable rear right seat heating
      required: false
      selector:
        boolean:

refresh_cloud_data:
  name: Refresh cloud data
  description: Refresh data from the cloud for all vehicles
  fields: {}

start_auxiliary_heating:
  name: Start auxiliary heating
  description: Start auxiliary heating with specified duration
  fields:
    vin:
      name: VIN
      description: Vehicle Identification Number
      required: true
      selector:
        text:
    duration:
      name: Duration
      description: Duration in minutes
      required: false
      default: 20
      selector:
        number:
          min: 5
          max: 60
          step: 5