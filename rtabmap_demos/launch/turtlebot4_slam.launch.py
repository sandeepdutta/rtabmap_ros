#
# Note: Make sure you have this fix for turtlebot4_description https://github.com/turtlebot/turtlebot4/pull/434,
#       otherwise, the lidar and camera point cloud won't be aligned correctly.
#
# Example with gazebo:
#   1) Launch simulator (turtlebot4 and nav2):
#     $ ros2 launch turtlebot4_ignition_bringup turtlebot4_ignition.launch.py slam:=false nav2:=true rviz:=true
#
#   2) Launch SLAM:
#     $ ros2 launch rtabmap_demos turtlebot4_slam.launch.py use_sim_time:=true qos:=2
#     OR
#     $ ros2 launch rtabmap_launch rtabmap.launch.py rtabmap_viz:=true subscribe_scan:=true rgbd_sync:=true depth_topic:=/oakd/rgb/preview/depth odom_sensor_sync:=true camera_info_topic:=/oakd/rgb/preview/camera_info rgb_topic:=/oakd/rgb/preview/image_raw visual_odometry:=false approx_sync:=true approx_rgbd_sync:=false odom_guess_frame_id:=odom icp_odometry:=true odom_topic:="icp_odom" map_topic:="/map" qos:=2 use_sim_time:=true odom_log_level:=warn rtabmap_args:="--delete_db_on_start --Reg/Strategy 1 --Reg/Force3DoF true --Mem/NotLinkedNodesKept false" use_action_for_goal:=true
#
#   3) Click on "Play" button on bottom-left of gazebo.
#
#   4) Click on double points ".." button on top-right next to power button to undock.
#
#   5) Teleop the robot:
#     $ ros2 run teleop_twist_keyboard teleop_twist_keyboard
#
#   6) Send goals with RVIZ's "Nav2 Goal" button in action bar:

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')
    qos = LaunchConfiguration('qos')
    localization = LaunchConfiguration('localization')

    icp_parameters={
          'odom_frame_id':'icp_odom',
          'guess_frame_id':'odom',
          'qos':qos
    }

    rtabmap_parameters={
          'subscribe_rgbd':True,
          'subscribe_scan':True,
          'use_action_for_goal':True,
          'odom_sensor_sync': True,
          'qos_scan':qos,
          'qos_image':qos,
          'qos_imu':qos,
          # RTAB-Map's parameters should be strings:
          'Mem/NotLinkedNodesKept':'false'
    }

    # Shared parameters between different nodes
    shared_parameters={
          'frame_id':'base_link',
          'use_sim_time':use_sim_time,
          # RTAB-Map's parameters should be strings:
          'Reg/Strategy':'1',
          'Reg/Force3DoF':'true',
          'Mem/NotLinkedNodesKept':'false'
    }

    remappings=[
          ('odom', 'icp_odom'),
          ('rgb/image', '/oakd/rgb/preview/image_raw'),
          ('rgb/camera_info', '/oakd/rgb/preview/camera_info'),
          ('depth/image', '/oakd/rgb/preview/depth')]

    return LaunchDescription([

        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time', default_value='false', choices=['true', 'false'],
            description='Use simulation (Gazebo) clock if true'),
        
        DeclareLaunchArgument(
            'qos', default_value='0',
            description='QoS used for input sensor topics'),
            
        DeclareLaunchArgument(
            'localization', default_value='false', choices=['true', 'false'],
            description='Launch rtabmap in localization mode (a map should have been already created).'),

        # Nodes to launch
        Node(
            package='rtabmap_sync', executable='rgbd_sync', output='screen',
            parameters=[{'approx_sync':False, 'use_sim_time':use_sim_time, 'qos':qos}],
            remappings=remappings),

        Node(
            package='rtabmap_odom', executable='icp_odometry', output='screen',
            parameters=[icp_parameters, shared_parameters],
            remappings=remappings,
            arguments=["--ros-args", "--log-level", 'icp_odometry:=warn']),

        # SLAM Mode:
        Node(
            condition=UnlessCondition(localization),
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=[rtabmap_parameters, shared_parameters],
            remappings=remappings,
            arguments=['-d']),
            
        # Localization mode:
        Node(
            condition=IfCondition(localization),
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=[rtabmap_parameters, shared_parameters,
              {'Mem/IncrementalMemory':'False',
               'Mem/InitWMWithAllNodes':'True'}],
            remappings=remappings),

        Node(
            package='rtabmap_viz', executable='rtabmap_viz', output='screen',
            parameters=[rtabmap_parameters, shared_parameters],
            remappings=remappings),
    ])