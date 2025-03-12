# -*- coding: utf-8 -*-
from abaqus import session
from odbAccess import openOdb
import csv

# --------------------------
# 用户输入配置
# --------------------------
# 通过对话框获取输入参数
inputs = getInputs(
    fields=(
        ('Number of instances:', '3'),  # 实例数量（默认值3）
        ('ODB file name:', 'Job-1.odb'),  # ODB文件名（默认Job-1.odb）
        ('Output CSV name:', 'HFL_Average.csv')  # 输出CSV文件名
    ),
    label='输入参数',
    dialogTitle='设置计算参数'
)
num_instances = int(inputs['Number of instances:'])  # 转换为整数
odb_name = inputs['ODB file name:']  # ODB文件名
csv_name = inputs['Output CSV name:']  # 输出文件名

# --------------------------
# 打开ODB文件并获取数据
# --------------------------
odb = session.openOdb(odb_name, readOnly=True)  # 以只读模式打开ODB文件
root_assembly = odb.rootAssembly  # 获取根装配体
step_name = 'Step-1'  # 指定分析步名称
last_frame = odb.steps[step_name].frames[-1]  # 获取最后一帧数据

# --------------------------
# 初始化CSV文件
# --------------------------
with open(csv_name, 'w', newline='') as csvfile:  # 安全打开文件（自动关闭）
    writer = csv.writer(csvfile)
    writer.writerow(['HFL_Magnitude', 'HFL_X', 'HFL_Y', 'HFL_Z'])  # 写入表头

    # --------------------------
    # 遍历所有实例计算体积加权平均
    # --------------------------
    for instance_id in range(1, num_instances + 1):  # 实例编号从1开始
        instance_name = f'PART-{instance_id}-1'  # 生成实例名称（例如PART-1-1）

        try:
            instance = root_assembly.instances[instance_name]  # 获取实例对象
        except KeyError:
            print(f"警告：实例 {instance_name} 不存在，跳过计算")
            continue

        # 提取当前实例的IVOL（体积）和HFL（热流）数据
        vol_data = last_frame.fieldOutputs['IVOL'].getSubset(region=instance).values
        hfl_data = last_frame.fieldOutputs['HFL'].getSubset(region=instance).values

        # --------------------------
        # 初始化累加变量
        # --------------------------
        total_volume = 0.0
        sum_hfl_magnitude = 0.0
        sum_hfl_x = 0.0
        sum_hfl_y = 0.0
        sum_hfl_z = 0.0

        # --------------------------
        # 遍历单元计算加权和
        # --------------------------
        for vol, hfl in zip(vol_data, hfl_data):  # 同时遍历体积和热流数据
            cell_volume = vol.data
            hfl_magnitude = hfl.magnitude
            hfl_x = hfl.data[0]
            hfl_y = hfl.data[1]
            hfl_z = hfl.data[2]

            # 累加体积加权值
            total_volume += cell_volume
            sum_hfl_magnitude += hfl_magnitude * cell_volume
            sum_hfl_x += hfl_x * cell_volume
            sum_hfl_y += hfl_y * cell_volume
            sum_hfl_z += hfl_z * cell_volume

        # --------------------------
        # 计算平均值（防止除零）
        # --------------------------
        if total_volume > 1e-10:  # 忽略微小体积
            avg_magnitude = sum_hfl_magnitude / total_volume
            avg_x = sum_hfl_x / total_volume
            avg_y = sum_hfl_y / total_volume
            avg_z = sum_hfl_z / total_volume
        else:
            avg_magnitude = avg_x = avg_y = avg_z = 0.0

        # --------------------------
        # 写入CSV
        # --------------------------
        writer.writerow([
            round(avg_magnitude, 6),
            round(avg_x, 6),
            round(avg_y, 6),
            round(avg_z, 6)
        ])
        print(f"实例 {instance_name} 计算完成")

# --------------------------
# 清理资源
# --------------------------
odb.close()  # 显式关闭ODB文件
print("计算完成！结果已保存至", csv_name)