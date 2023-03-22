"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process, Manager, Value


# Datos de control del programa
NORTE = 0
SUR = 1

NCARS = 100
NPED = 10

TIME_CARS_NORTH = 0.5   # Delay de la produccion de vehiculos en direccion norte
TIME_CARS_SOUTH = 0.5   # Delay de la produccion de vehiculos en direccion sur
TIME_PED = 5            # Delay de la produccion de peatones

TIME_IN_BRIDGE_CARS = (1, 0.5)          # Tiempo que tarda un vehiculo en cruzar el puente en cualquier direccion
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10)    # Tiempo que tarda una peaton en cruzar el puente en cualquier direccion

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.contador = Value('i', 0) # Numero de llamadas realizadas a metodos del monitor
        
        # Valores compartidos
        self.nVehiN = Value('i', 0) # Numero de vehiculos que hay en el puente que van en direccion norte
        self.nVehiS = Value('i', 0) # Numero de vehiculos que hay en el puente que van en direccion sur
        self.nPeat = Value('i', 0) # Numero de peatones que hay en el puente (no nos importa la direccion)
        
        self.wVehiN = Value('i', 0) # Numero de vehiculos esperando para tomar direccion norte
        self.wVehiS = Value('i', 0) # Numero de vehiculos esperando para tomar direccion sur
        self.wPeat = Value('i', 0) # Numero de peatones esperando
        
        m = Manager()
        self.puente = m.list()
        
        # Variables de Condicion
        self.N_puente = Condition(self.mutex)
        self.S_puente = Condition(self.mutex)
        self.P_puente = Condition(self.mutex)
        
        self.N_espera = Condition(self.mutex)
        self.S_espera = Condition(self.mutex)
        self.P_espera = Condition(self.mutex)
        
    def __repr__(self):
        return f"{self.contador.value}. Monitor: {self.puente}"
    
    
    # Funciones Boooleanas para las condiciones
    
    def puede_entrar_N(self) -> bool:
        return self.nVehiS.value == 0 and self.nPeat.value == 0 #Esto hay que ver como lo limitamos si queremos que pueda entrar mas de uno and self.n_north.value == 0
    
    def puede_entrar_S(self) -> bool:
        return self.nVehiN.value == 0 and self.nPeat.value == 0 #and self.n_south.value == 0 
    
    def puede_entrar_P(self) -> bool:
        return self.nVehiN.value == 0 and self.nVehiS.value == 0 

    def puede_esperar_N(self) -> bool:
        return self.nVehiN.value == 0 or self.wVehiS.value + self.wPeat.value == 0
    
    def puede_esperar_S(self) -> bool:
        return self.nVehiS.value == 0 or self.wPeat.value + self.wVehiN.value == 0 
    
    def puede_esperar_P(self) -> bool:
        return self.nPeat.value == 0 or self.wVehiS.value + self.wVehiN.value == 0 


    # Funciones de control del Monitor
    
    def wants_enter_car(self, direccion: int) -> None:
        with self.mutex:
            self.contador.value += 1
            if direccion == 0:
                self.N_espera.wait_for(self.puede_esperar_N())
                self.wVehiN.value += 1
                self.N_puente.wait_for(self.puede_entrar_N)
                self.wVehiN.value -= 1
                self.nVehiN.value += 1
                #self.puente.append(algo)
                self.S_espera.notify_all()
                self.P_espera.notify_all()
            
            else:
                self.S_espera.wait_for(self.puede_esperar_S())
                self.wVehiS.value += 1
                self.S_puente.wait_for(self.puede_entrar_S)
                self.wVehiS.value -= 1
                self.nVehiS.value += 1
                #self.puente.append(algo)
                self.P_espera.notify_all()
                self.N_espera.notify_all()
    
    def leaves_car(self, direccion: int) -> None:
        with self.mutex:
            self.contador.value += 1
            if direccion == 0:
                #self.puente remove algo
                self.nVehiN.value -= 1
                self.S_puente.notify_all()
                self.P_puente.notify_all()
            else:
                #self.puente remove algo
                self.nVehiS.value -= 1
                self.P_puente.notify_all()
                self.N_puente.notify_all()
                
    def wants_enter_pedestrian(self) -> None:
        with self.mutex:
            self.contador.value += 1
            self.P_espera.wait_for(self.puede_esperar_P())
            self.wPeat.value += 1
            self.P_puente.wait_for(self.puede_entrar_P)
            self.wPeat.value -= 1
            self.nPeat.value += 1
            #self.puente.append(algo)
            self.N_espera.notify_all()
            self.S_espera.notify_all()
        
    def leaves_pedestrian(self) -> None:
        with self.mutex:
            self.contador.value += 1
            #self.puente remove algo
            self.nPeat.value -= 1
            self.N_puente.notify_all()
            self.S_puente.notify_all()


def delay_car_north() -> None:
    pass

def delay_car_south() -> None:
    pass

def delay_pedestrian() -> None:
    pass

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()
