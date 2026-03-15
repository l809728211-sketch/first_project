import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    # 1. 获取功能包的路径
    pkg_name = 'my_robot_description'
    pkg_share = get_package_share_directory(pkg_name)

    # 2. 解析 Xacro 文件并转换为 URDF 字符串
    xacro_file = os.path.join(pkg_share, 'urdf', 'sensors_setup.urdf.xacro')
    doc = xacro.process_file(xacro_file)
    robot_description = {'robot_description': doc.toxml()}

    # 3. 启动 robot_state_publisher 节点，发布 TF 树
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # 4. 包含 Gazebo 的启动文件，并加载我们自定义的 test_env.world
    world_path = os.path.join(pkg_share, 'worlds', 'custom_env.world')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')
    
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_path}.items()
    )

    # 5. 使用 spawn_entity.py 将 URDF 模型动态生成到 Gazebo 中
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'sensor_car',
            '-x', '0.0', '-y', '0.0', '-z', '0.1' # 初始生成位置
        ],
        output='screen'
    )

    # 6. 返回并执行所有定义好的动作
    return LaunchDescription([
        node_robot_state_publisher,
        gazebo_launch,
        spawn_entity
    ])
