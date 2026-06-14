from setuptools import find_packages, setup

package_name = 'mi_tortuga'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Julian',
    maintainer_email='jjjuliiian1@gmail.com',
    description='Controlador de TurtleSim',
    license='MIT',
    entry_points={
        'console_scripts': [
            'controlador = mi_tortuga.controlador:main',
        ],
    },
)
