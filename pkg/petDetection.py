# pet detection stub
import random
import time

random.seed(time.time())
def classifyPet(imagePath):
    selector=random.randint(0,29)
    return (selector % 3) # 0 = no pet, 1 = cat, 2 = dog, etc.
