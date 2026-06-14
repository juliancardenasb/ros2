from setuptools import find_packages, setup

package_name = 'control_teclado'

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
    description='Control de TurtleSim por teclado',
    license='MIT',
    entry_points={
        'console_scripts': [
            'teclado = control_teclado.teclado:main',
        ],
    },
)
