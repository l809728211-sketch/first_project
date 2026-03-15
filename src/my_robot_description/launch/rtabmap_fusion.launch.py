import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    # 全局参数：在仿真环境下，必须强制使用仿真时间
    use_sim_time = True

    # 传感器话题重映射
    remappings = [
        ('rgb/image', '/camera/color/image_raw'),
        ('depth/image', '/camera/depth/image_raw'),
        ('rgb/camera_info', '/camera/color/camera_info'),
        ('scan_cloud', '/livox/lidar')
    ]

    # RTAB-Map 核心参数配置
    parameters = [{
        'frame_id': 'base_link',
        'use_sim_time': use_sim_time,
        'subscribe_depth': True,        # 订阅深度相机
        'subscribe_scan_cloud': True,   # 订阅 3D 激光雷达
        'approx_sync': True,            # 开启近似同步（解决传感器频率不一致、时间戳对不齐的问题）
        'queue_size': 30,               # 增大队列，防止虚拟机卡顿时丢帧
        
        # 里程计与建图策略
        'Reg/Strategy': '1',            # 0=视觉, 1=ICP(激光), 2=视觉+ICP。这里选1，用雷达做主力匹配
        'RGBD/NeighborLinkRefining': 'true',
        
        # 针对 3D 雷达的点云处理（重要：降低 CPU 负载）
        'Icp/VoxelSize': '0.1',         # 激光点云体素滤波大小 (10cm)
        'Icp/PointToPlane': 'true',     # 使用点到面 ICP
        
        # 2D 栅格地图生成 (为 Nav2 提供全局地图)
        'Grid/From3D': 'true',          # 从 3D 点云投影生成 2D 占据栅格
        'Grid/Sensor': '2',             # 0=激光雷达(2D), 1=深度相机, 2=3D激光点云。选2，利用全向雷达
        'Grid/CellSize': '0.05',        # 栅格地图分辨率 5cm
        'Grid/MaxObstacleHeight': '2.0',
        'Grid/MinObstacleHeight': '0.0' # 确保能扫描到低矮障碍物
    }]

    # 1. 启动 RGB-D 里程计节点
    # 作用：计算机器人在世界坐标系下的实时位姿，并发布 /odom -> /base_link 的 TF
    rgbd_odometry_node = Node(
        package='rtabmap_odom',
        executable='rgbd_odometry',
        output='screen',
        parameters=parameters,
        remappings=remappings
    )

    # 2. 启动 RTAB-Map 核心建图节点
    # 作用：接收里程计、图像和点云，构建全局 3D 地图，并发布用于导航的 2D map
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        output='screen',
        parameters=parameters,
        remappings=remappings,
        arguments=['-d'] # -d 参数表示每次启动时清空之前的旧地图库
    )

    # 3. 启动 RTAB-Map 可视化工具 (可选，你也可以在 RViz2 中查看)
    rtabmap_viz_node = Node(
        package='rtabmap_viz',
        executable='rtabmap_viz',
        output='screen',
        parameters=parameters,
        remappings=remappings
    )

    return LaunchDescription([
        rgbd_odometry_node,
        rtabmap_node,
        rtabmap_viz_node
    ])
