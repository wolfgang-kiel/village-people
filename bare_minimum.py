
# coding: utf-8

# In[82]:


import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import random


# In[271]:


def skillcheck(bonus,dc):
    return random.randint(1,20) - dc + bonus
def roll(n=1,sides=6):
    return np.random.randint(1,sides+1,n).sum()


# In[333]:


class BuildingType:
    def __init__(self,name,requires,operate_skill,operate_pop,goods_produced,build_skills,build_points,build_dc):
        self.name = name
        self.requires = requires
        self.operate_skill = operate_skill
        self.operate_pop = operate_pop
        self.goods_produced = goods_produced
        self.build_skills = build_skills
        self.build_points = build_points
        self.build_dc = build_dc
    def __repr__(self):
        return self.name

farm = BuildingType("Farm",[],["farmer"],10,{"food":25},["farmer"],4,12)

# In[334]:


class Ruleset:
    def __init__(self,building_types):
        self.building_types = building_types
        self.buildable_with = defaultdict(list)
        self.all_skills = set()
        self.all_goods = set()
        
        for building in building_types:
            for skill in building.build_skills:
                self.buildable_with[skill].append(building) 
                self.all_skills.add(skill)
            for skill in building.operate_skill:
                self.all_skills.add(skill)
            for good in building.goods_produced:
                self.all_goods.add(good)
        
    def build_priority(self,village,options):
        """Select from a number of building options
        """
        return farm
        highest_priority = []
        if village.goods_produced["food"] < village.total_pop:
            highest_priority = [farm] # Is there a better way? Here i'm referring to global object...
        # TODO: Add more priorities
        
        for hp in highest_priority:
            if hp in options:
                return hp
        # No priority applies
        # Check if one of options already under construction
        if set(options).intersection(village.projects):
            return random.sample(set(options).intersection(village.projects),1)[0]
        # Otherwise just build anything
        return random.choice(options)
    
    def get_random_skill(self):
        return random.sample(self.all_skills,1)[0]

    def get_growth_check_bonus(self,village):
        bonus = 0
        for good in ["goods","trade","defense"]:
            bonus += village.goods_produced[good]/50
        if village.total_pop > village.goods_produced["food"]:
            bonus = bonus - village.total_pop + village.goods_produced["food"]
        # TODO: Missing death and attacks and such
        return bonus


# In[335]:


rules = Ruleset([farm])
from collections import Counter
class Village:
    def __init__(self,population,buildings,ruleset):
        self.population = Counter(population) # Dict: string (skill) -> int
        self.buildings = Counter(buildings) # Dict: Building type -> int
        self.available = Counter(population)
        self.goods_produced = Counter()
        self.projects = Counter()
        self.ruleset = ruleset
        self.failed_learning = Counter()
    @property
    def total_pop(self):
        return sum(self.population.values())
    def assign_workers(self):
        available = self.population.copy()
        active_buildings = Counter()
        inactive_buildings = Counter()
        for building in self.buildings.elements():
            for skill in building.operate_skill:
                #print 'Looking for ',skill,'found ',available[skill],' and ',available['none'], ' pop'
                if available[skill] > 0 and available["none"]>=building.operate_pop:
                    available[skill] -= 1
                    available["none"] -= building.operate_pop
                    active_buildings[building] += 1
                    break
                else:
                    inactive_buildings[building] += 1
        self.active_buildings = active_buildings
        self.inactive_buildings = inactive_buildings
        self.available = available
        
        self.goods_produced = Counter()
        for building in self.active_buildings:
            for good in building.goods_produced:
                self.goods_produced[good] += building.goods_produced[good]
        
    def npc_build(self):
        for skill in self.available.elements():
            if skill=="none":
                continue
            elif not skill in self.ruleset.buildable_with:
                continue
            else:
                options = self.ruleset.buildable_with[skill]
                valid_options = []
                for op in options:
                    if not op.requires:
                        valid_options.append(op)
                        continue
                    
                    for req in op.requires:
                        if isinstance(req,list):
                            # List means ALL are required
                            if set(req).issubset(self.active_buildings):
                                valid_options.append(op)
                                break
                        else:
                            if req in self.active_buildings:
                                valid_options.append(op)
                                break
                if valid_options:
                    decision = self.ruleset.build_priority(self,valid_options)
                    print skill,' builds ', decision
                    u = skillcheck(4,decision.build_dc)
                    if u>0:
                        self.projects[decision] += 1 + u/5
                        if self.projects[decision] >= decision.build_points:
                            self.projects[decision] = 0
                            self.buildings[decision] += 1
    
    def learning_check(self):     
        if self.population["none"] == 0:
            print 'Nobody here can learn anything'
            return
        skill = self.ruleset.get_random_skill()
        bonus = self.population[skill] + 2 * self.failed_learning[skill]
        for building in self.buildings:
            if building.operate_skill == skill:
                bonus += self.buildings[building]
        
        if skillcheck(bonus,15)>0:
            self.population["none"] -= 1
            self.population[skill] += 1
            print 'We have a new', skill
        else:
            self.failed_learning[skill] += 1
    
    def growth_check(self):
        # Shouldnt this be in ruleset?
        bonus = self.ruleset.get_growth_check_bonus(self)
        u = skillcheck(bonus,0)
        print 'Growth check: %d (%d)' % (u,bonus)
        pop_growth = 0
        new_pop = []
        
        if u<5:
            pop_spec = [e for e in champ.population.elements() if e!='none']
            leaves = random.choice(pop_spec)
            print 'a ',leaves,' leaves'
            self.population[leaves] -= 1
            pop_growth = -roll(2,6)
        elif u<20:
            pop_growth =  roll(1,6)
        elif u<25:
            pop_growth = roll(1,6)
            new_pop = [self.ruleset.get_random_skill()]
        elif u<30:
            pop_growth = roll(2,6)
            new_pop = [self.ruleset.get_random_skill()]
        elif u<35:
            pop_growth = roll(3,6)
            new_pop = [self.ruleset.get_random_skill()]            
        elif u<40:
            pop_growth = roll(4,6)
            new_pop = [self.ruleset.get_random_skill()] 
        elif u<50:
            pop_growth = roll(4,6)
            new_pop = [self.ruleset.get_random_skill(),self.ruleset.get_random_skill()]  
        else:
            pop_growth = roll(5,6)
            new_pop = [self.ruleset.get_random_skill(),self.ruleset.get_random_skill()]  
        
        self.population['none'] += pop_growth
        self.population['none'] = max(0,self.population['none'])
        print 'Town grows by',pop_growth
        for p in new_pop:
            self.population[p] += 1
            print 'A new ',p,' comes to town'


champ = Village({"farmer":1,"none":10},{farm:1},rules)

champ.assign_workers()
for i in range(100):
    champ.assign_workers()
    champ.npc_build()