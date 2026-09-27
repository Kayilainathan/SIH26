import cv2
import numpy as np
import random
import math

def generate_ore_polygon(radius):
    """Generates irregular polygons to simulate raw iron ore chunks."""
    points = []
    for angle in range(0, 360, 45):
        # Add random jaggedness to the rock shape
        r = radius + random.randint(-int(radius*0.3), int(radius*0.3))
        x = int(r * math.cos(math.radians(angle)))
        y = int(r * math.sin(math.radians(angle)))
        points.append([x, y])
    return np.array(points)

def main():
    # Simulation Window Settings
    width, height = 800, 600
    true_center = int(width / 2)
    belt_width = 300
    belt_speed = 6
    
    # Physical Variables to Simulate
    drift = 0.0          # Lateral mistracking in pixels
    drift_target = 0.0   # Where the belt is trying to drift
    ores = []            # Active iron ore objects on belt
    
    print("Starting SIH26008 Conveyor Vision Simulation... Press 'ESC' to exit.")
    
    # Frame generation loop
    frame_count = 0
    while True:
        frame_count += 1
        
        # 1. GENERATE THE SYNTHETIC ENVIRONMENT
        frame = np.ones((height, width, 3), dtype=np.uint8) * 50 # Dark industrial floor
        
        # Simulate mechanical drift (Belt Mistracking)
        if frame_count % 60 == 0:
            if random.random() < 0.15:
                drift_target = random.randint(-70, 70) # Severe drift event
            else:
                drift_target = random.randint(-15, 15) # Normal running variance
                
        drift += (drift_target - drift) * 0.05 # Smooth mechanical transition
        belt_x1 = int(true_center - belt_width/2 + drift)
        belt_x2 = int(true_center + belt_width/2 + drift)
        
        # Draw Steel Gantry Structure
        cv2.rectangle(frame, (200, 0), (220, height), (100, 100, 100), -1)
        cv2.rectangle(frame, (580, 0), (600, height), (100, 100, 100), -1)
        
        # Draw Rotating Idler Rollers
        for y in range(0, height + 100, 100):
            offset_y = (y + (frame_count * belt_speed)) % (height + 100) - 50
            cv2.line(frame, (220, int(offset_y)), (580, int(offset_y)), (70, 70, 70), 12)
            
        # Draw the Rubber Belt
        cv2.rectangle(frame, (belt_x1, 0), (belt_x2, height), (35, 35, 35), -1)
        
        # 2. SIMULATE IRON ORE LOADING
        if random.random() < 0.10: # Spawn probability
            if random.random() < 0.08:
                # Simulate a massive surge/spillage risk
                base_size = random.randint(40, 70)
                num_rocks = random.randint(3, 5)
            else:
                # Normal loading
                base_size = random.randint(15, 30)
                num_rocks = 1
                
            for _ in range(num_rocks):
                # Ensure rocks spawn inside the belt margins
                ox = random.randint(belt_x1 + base_size, belt_x2 - base_size)
                ores.append({
                    "pos": [ox, -base_size], 
                    "poly": generate_ore_polygon(base_size), 
                    "color": (40, 50, 70) # Dark brown/gray iron ore
                })
        
        # Draw and move the Iron Ore
        total_ore_area = 0
        for ore in ores:
            ore["pos"][1] += belt_speed
            pts = ore["poly"] + ore["pos"]
            total_ore_area += cv2.contourArea(pts) # Calculate pixel volume
            cv2.fillPoly(frame, [pts], ore["color"])
            cv2.polylines(frame, [pts], True, (60, 70, 90), 1)
            
        # Remove rocks that fell off the screen
        ores = [ore for ore in ores if ore["pos"][1] < height + 100]
        
        # 3. AI VISION PROCESSING LOGIC (The SIH Solution)
        # Evaluate Mistracking
        deviation = abs(drift)
        alarm_mistrack = deviation > 35
        
        if alarm_mistrack:
            # Highlight edges in RED for deviation
            cv2.line(frame, (belt_x1, 0), (belt_x1, height), (0, 0, 255), 6)
            cv2.line(frame, (belt_x2, 0), (belt_x2, height), (0, 0, 255), 6)
        else:
            # Safe margins in GREEN
            cv2.line(frame, (belt_x1, 0), (belt_x1, height), (0, 255, 0), 2)
            cv2.line(frame, (belt_x2, 0), (belt_x2, height), (0, 255, 0), 2)
            
        # Evaluate Overload / Spillage
        max_safe_area = 65000 # Tunable pixel threshold for max belt capacity
        load_pct = (total_ore_area / max_safe_area) * 100
        alarm_overload = load_pct > 85
        
        if alarm_overload:
            cv2.rectangle(frame, (belt_x1+5, 150), (belt_x2-5, height-150), (0, 0, 255), 3)
            cv2.putText(frame, "WARNING: MASS OVERLOAD Sensed", (belt_x1+15, 190), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
        # 4. SCADA / DASHBOARD OVERLAY
        # This proves the OpenCV data is ready for Streamlit/Digital Twin integration
        cv2.rectangle(frame, (10, 10), (370, 170), (10, 10, 10), -1)
        cv2.rectangle(frame, (10, 10), (370, 170), (255, 255, 255), 1)
        
        cv2.putText(frame, "SIH26008: AI VISION EDGE NODE", (20, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        track_color = (0, 0, 255) if alarm_mistrack else (0, 255, 0)
        cv2.putText(frame, f"LATERAL DRIFT: {deviation:.1f} mm", (20, 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, track_color, 2)
        
        load_color = (0, 0, 255) if alarm_overload else (0, 255, 0)
        cv2.putText(frame, f"VOLUMETRIC LOAD: {load_pct:.1f}%", (20, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, load_color, 2)
        
        status_text = "E-STOP RELAY TRIGGERED!" if (alarm_mistrack or alarm_overload) else "SYSTEM STATUS: NOMINAL"
        status_color = (0, 0, 255) if (alarm_mistrack or alarm_overload) else (0, 255, 0)
        cv2.putText(frame, status_text, (20, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Display the result
        cv2.imshow("Conveyor Vision Pipeline Simulation", frame)
        
        # Exit on 'ESC'
        if cv2.waitKey(30) & 0xFF == 27:
            break
            
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()