from setuptools import find_packages, setup

package_name = 'assignment1_rt'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pouln',
    maintainer_email='pouln@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
	entry_points={
   	 'console_scripts':
	 [
       	'ui = assignment1_rt.ui_node:main',
        'distance = assignment1_rt.distance_node:main',
        'turtle_spawn = assignment1_rt.turtle_spawn:main',
   	 ],
},

)
