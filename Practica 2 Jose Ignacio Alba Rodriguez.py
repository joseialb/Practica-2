"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process, Manager, Value


# Datos de control del programa
NORTE = 0
SUR = 1

NCARS = 20
NPED = 20

TIME_CARS_NORTH = 5     # Delay de la produccion de vehiculos en direccion norte
TIME_CARS_SOUTH = 5     # Delay de la produccion de vehiculos en direccion sur
TIME_PED = 3            # Delay de la produccion de peatones

TIME_IN_BRIDGE_CARS = (10, 1)          # Tiempo que tarda un vehiculo en cruzar el puente en cualquier direccion
TIME_IN_BRIDGE_PEDESTRIAN = (20, 5)    # Tiempo que tarda una peaton en cruzar el puente en cualquier direccion

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
        return self.nVehiS.value == 0 and self.nPeat.value == 0 
    
    def puede_entrar_S(self) -> bool:
        return self.nVehiN.value == 0 and self.nPeat.value == 0 
    
    def puede_entrar_P(self) -> bool:
        return self.nVehiN.value == 0 and self.nVehiS.value == 0 

    def puede_esperar_N(self) -> bool:
        return self.nVehiN.value == 0 or self.wVehiS.value + self.wPeat.value == 0
    
    def puede_esperar_S(self) -> bool:
        return self.nVehiS.value == 0 or self.wPeat.value + self.wVehiN.value == 0 
    
    def puede_esperar_P(self) -> bool:
        return self.nPeat.value == 0 or self.wVehiS.value + self.wVehiN.value == 0 


    # Funciones de control del Monitor
    
    def wants_enter_car(self, direccion: int, c_id) -> None:
        with self.mutex:
            self.contador.value += 1
            if direccion == 0:
                print(f"El vehiculo {c_id} N quiere esperar para entrar al puente")
                self.N_espera.wait_for(self.puede_esperar_N)
                print(f"El vehiculo {c_id} N está esperando a entrar\n{self}")
                self.wVehiN.value += 1
                self.N_puente.wait_for(self.puede_entrar_N)
                self.wVehiN.value -= 1
                self.nVehiN.value += 1
                self.puente.append(f"Vehiculo {c_id} N")
                print(f"El vehiculo {c_id} N ha entrado al puente\n{self}")
                self.S_espera.notify_all()
                self.P_espera.notify_all()
            
            else:
                print(f"El vehiculo {c_id} S quiere esperar para entrar al puente")
                self.S_espera.wait_for(self.puede_esperar_S)
                print(f"El vehiculo {c_id} S está esperando a entrar\n{self}")
                self.wVehiS.value += 1
                self.S_puente.wait_for(self.puede_entrar_S)
                self.wVehiS.value -= 1
                self.nVehiS.value += 1
                self.puente.append(f"Vehiculo {c_id} S")
                print(f"El vehiculo {c_id} S ha entrado al puente\n{self}")
                self.P_espera.notify_all()
                self.N_espera.notify_all()
    
    def leaves_car(self, direccion: int, c_id: int )-> None:
        with self.mutex:
            self.contador.value += 1
            if direccion == 0:
                self.puente.remove(f"Vehiculo {c_id} N")
                print(f"El vehiculo {c_id} N ha salido del puente\n{self}")
                self.nVehiN.value -= 1
                self.S_puente.notify_all()
                self.P_puente.notify_all()
            else:
                self.puente.remove(f"Vehiculo {c_id} S")
                print(f"El vehiculo {c_id} S ha salido del puente\n{self}")
                self.nVehiS.value -= 1
                self.P_puente.notify_all()
                self.N_puente.notify_all()
                
    def wants_enter_pedestrian(self, p_id) -> None:
        with self.mutex:
            print(f"El Peaton {p_id} quiere esperar para entrar al puente")
            self.contador.value += 1
            self.P_espera.wait_for(self.puede_esperar_P)
            print(f"El Peaton {p_id} está esperando a entrar\n{self}")
            self.wPeat.value += 1
            self.P_puente.wait_for(self.puede_entrar_P)
            self.wPeat.value -= 1
            self.nPeat.value += 1
            self.puente.append(f"Peaton {p_id}")
            print(f"El Peaton {p_id} ha entrado al puente\n{self}")
            self.N_espera.notify_all()
            self.S_espera.notify_all()
        
    def leaves_pedestrian(self, p_id) -> None:
        with self.mutex:
            self.contador.value += 1
            self.puente.remove(f"Peaton {p_id}")
            print(f"El Peaton {p_id} ha salido del puente\n{self}")
            self.nPeat.value -= 1
            self.N_puente.notify_all()
            self.S_puente.notify_all()


def delay_car_north() -> None:
    m,d = TIME_IN_BRIDGE_CARS
    a = random.uniform(m,d)
    time.sleep(a)

def delay_car_south() -> None:
    m,d = TIME_IN_BRIDGE_CARS
    a = random.uniform(m,d)
    time.sleep(a)

def delay_pedestrian() -> None:
    m,d = TIME_IN_BRIDGE_PEDESTRIAN
    a = random.uniform(m,d)
    time.sleep(a)

def car(cid: int, direccion: int, monitor: Monitor)  -> None:
    monitor.wants_enter_car(direccion, cid)
    if direccion== 0 :
        delay_car_north()
    else:
        delay_car_south()
    monitor.leaves_car(direccion, cid)

def pedestrian(pid: int, monitor: Monitor) -> None:
    monitor.wants_enter_pedestrian(pid)
    delay_pedestrian()
    monitor.leaves_pedestrian(pid)


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
    gcars_north = Process(target=gen_cars, args=(NORTE, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SUR, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()