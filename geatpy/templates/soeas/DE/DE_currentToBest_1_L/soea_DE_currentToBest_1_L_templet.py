# -*- coding: utf-8 -*-
import geatpy as ea # 导入geatpy库
import numpy as np
from sys import path as paths
from os import path
paths.append(path.split(path.split(path.realpath(__file__))[0])[0])

class soea_DE_currentToBest_1_L_templet(ea.SoeaAlgorithm):
    
    """
soea_DE_currentToBest_1_L_templet : class - 差分进化DE/current-to-best/1/bin算法模板

算法描述:
    为了实现矩阵化计算，本模板采用打乱个体顺序来代替随机选择差分向量。算法流程如下：
    1) 初始化候选解种群。
    2) 若满足停止条件则停止，否则继续执行。
    3) 对当前种群进行统计分析，比如记录其最优个体、平均适应度等等。
    4) 采用current-to-best的方法选择差分变异的各个向量，对当前种群进行差分变异，得到变异个体。
    5) 将当前种群和变异个体合并，采用指数交叉方法得到试验种群。
    6) 在当前种群和实验种群之间采用一对一生存者选择方法得到新一代种群。
    7) 回到第2步。

参考文献:
    [1] Das, Swagatam & Suganthan, Ponnuthurai. (2011). Differential Evolution: 
        A Survey of the State-of-the-Art.. IEEE Trans. Evolutionary Computation. 15. 4-31.

"""
    
    def __init__(self, problem, population):
        ea.SoeaAlgorithm.__init__(self, problem, population) # 先调用父类构造方法
        if population.ChromNum != 1:
            raise RuntimeError('传入的种群对象必须是单染色体的种群类型。')
        self.name = 'DE/current-to-best/1/L'
        if population.Encoding == 'RI':
            self.mutOper = ea.Mutde(F = 0.5) # 生成差分变异算子对象
            self.recOper = ea.Xovexp(XOVR = 0.5, Half = True) # 生成指数交叉算子对象，这里的XOVR即为DE中的Cr
        else:
            raise RuntimeError('编码方式必须为''RI''.')
        
    def run(self, prophetPop = None): # prophetPop为先知种群（即包含先验知识的种群）
        #==========================初始化配置===========================
        population = self.population
        NIND = population.sizes
        self.initialization() # 初始化算法模板的一些动态参数
        #===========================准备进化============================
        if population.Chrom is None:
            population.initChrom(NIND) # 初始化种群染色体矩阵
        self.call_aimFunc(population) # 计算种群的目标函数值
        # 插入先验知识（注意：这里不会对先知种群prophetPop的合法性进行检查，故应确保prophetPop是一个种群类且拥有合法的Chrom、ObjV、Phen等属性）
        if prophetPop is not None:
            population = (prophetPop + population)[:NIND] # 插入先知种群
        population.FitnV = ea.scaling(self.problem.maxormins * population.ObjV, population.CV) # 计算适应度
        #===========================开始进化============================
        while self.terminated(population) == False:
            # 进行差分进化操作
            r0 = np.array(range(NIND))
            r_best = ea.selecting('ecs', population.FitnV, NIND) # 执行'ecs'精英复制选择
            r1 = None # 设置为None是为了传入变异算子后被设置为默认值
            r2 = None # 设置为None是为了传入变异算子后被设置为默认值
            experimentPop = population.copy() # 存储试验个体
            experimentPop.Chrom = self.mutOper.do(experimentPop.Encoding, experimentPop.Chrom, experimentPop.Field, [r0, r1, r2, r_best, r0]) # 变异
            tempPop = population + experimentPop # 当代种群个体与变异个体进行合并（为的是后面用于重组）
            experimentPop.Chrom = self.recOper.do(tempPop.Chrom) # 重组
            self.call_aimFunc(experimentPop) # 计算目标函数值
            tempPop = population + experimentPop # 临时合并，以调用otos进行一对一生存者选择
            tempPop.FitnV = ea.scaling(self.problem.maxormins * tempPop.ObjV, tempPop.CV) # 计算适应度
            population = tempPop[ea.selecting('otos', tempPop.FitnV, NIND)] # 采用One-to-One Survivor选择，产生新一代种群
        
        return self.finishing(population) # 调用finishing完成后续工作并返回结果
