# Software F1 - Sistema Integral de Gestion de Clientes, Servicios y Reservas
# Curso Programacion 213023 - Fase 4 - Manejo avanzado de excepciones
# Sin base de datos: toda la gestion con objetos, listas y archivo de log

from abc import ABC, abstractmethod
from datetime import datetime

# ---------- ARCHIVO DE LOG ----------
def registrar_log(mensaje):
    """Escribe cada error/evento en errores.log con fecha y hora."""
    try:
        with open("errores.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {mensaje}\n")
    except Exception as e:
        print(f"No se pudo escribir el log: {e}")

# ---------- EXCEPCIONES PERSONALIZADAS ----------
class DatoInvalidoError(Exception): pass
class ClienteNoEncontradoError(Exception): pass
class ServicioNoDisponibleError(Exception): pass
class ReservaInvalidaError(Exception): pass
class OperacionNoPermitidaError(Exception): pass

# ---------- CLASE ABSTRACTA: ENTIDAD ----------
class Entidad(ABC):
    """Clase abstracta que representa entidades generales del sistema."""
    def __init__(self, id_entidad, nombre):
        if not nombre or not str(nombre).strip():
            raise DatoInvalidoError("El nombre no puede estar vacio.")
        self._id = id_entidad
        self._nombre = nombre
    @property
    def id(self): return self._id
    @property
    def nombre(self): return self._nombre
    @abstractmethod
    def mostrar_info(self): pass

# ---------- CLASE CLIENTE ----------
class Cliente(Entidad):
    """Cliente con validaciones robustas y encapsulacion."""
    def __init__(self, id_cliente, nombre, correo, telefono):
        super().__init__(id_cliente, nombre)
        if "@" not in str(correo) or "." not in str(correo):
            raise DatoInvalidoError(f"Correo invalido: {correo}")
        if len(str(telefono)) < 7:
            raise DatoInvalidoError("Telefono invalido: debe tener al menos 7 digitos.")
        self._correo = correo
        self._telefono = telefono
    @property
    def correo(self): return self._correo
    @property
    def telefono(self): return self._telefono
    def mostrar_info(self):
        return f"Cliente {self._id}: {self._nombre} | {self._correo} | {self._telefono}"

# ---------- CLASE ABSTRACTA SERVICIO ----------
class Servicio(Entidad):
    """Servicio abstracto: define calcular_costo y describir."""
    def __init__(self, id_servicio, nombre, precio_base, disponible=True):
        super().__init__(id_servicio, nombre)
        if precio_base <= 0:
            raise DatoInvalidoError("El precio base debe ser mayor a 0.")
        self._precio_base = precio_base
        self._disponible = disponible
    @property
    def precio_base(self): return self._precio_base
    @property
    def disponible(self): return self._disponible
    @disponible.setter
    def disponible(self, valor): self._disponible = bool(valor)
    @abstractmethod
    def calcular_costo(self, duracion, impuesto=0.19, descuento=0): pass
    @abstractmethod
    def describir(self): pass
    def mostrar_info(self): return self.describir()
    def calcular_costo_con_opciones(self, duracion, impuesto=None, descuento=None, recargo_nocturno=0):
        imp = 0.19 if impuesto is None else impuesto
        desc = 0 if descuento is None else descuento
        return self.calcular_costo(duracion, impuesto=imp, descuento=desc) + recargo_nocturno

# ---------- 3 SERVICIOS ESPECIALIZADOS ----------
class AlquilerEquipo(Servicio):
    def __init__(self, id_servicio, nombre, precio_base, tipo_equipo):
        super().__init__(id_servicio, nombre, precio_base)
        self.tipo_equipo = tipo_equipo
    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        if duracion <= 0: raise DatoInvalidoError("La duracion debe ser mayor a 0.")
        if not (0 <= descuento <= 0.5): raise DatoInvalidoError("Descuento debe estar entre 0 y 0.5.")
        subtotal = self._precio_base * duracion
        return round(subtotal * (1 - descuento) * (1 + impuesto), 2)
    def describir(self): return f"[Alquiler] {self._nombre} - Equipo: {self.tipo_equipo} - ${self._precio_base}/dia"

class AsesoriaEspecializada(Servicio):
    def __init__(self, id_servicio, nombre, precio_base, especialista):
        super().__init__(id_servicio, nombre, precio_base)
        self.especialista = especialista
    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        if duracion <= 0: raise DatoInvalidoError("La duracion debe ser mayor a 0.")
        subtotal = self._precio_base * duracion + 50000
        return round(subtotal * (1 - descuento) * (1 + impuesto), 2)
    def describir(self): return f"[Asesoria] {self._nombre} - Especialista: {self.especialista} - ${self._precio_base}/hora"

class ReservaSala(Servicio):
    def __init__(self, id_servicio, nombre, precio_base, capacidad):
        super().__init__(id_servicio, nombre, precio_base)
        if capacidad <= 0: raise DatoInvalidoError("La capacidad debe ser mayor a 0.")
        self.capacidad = capacidad
    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        if duracion <= 0: raise DatoInvalidoError("La duracion debe ser mayor a 0.")
        subtotal = self._precio_base * duracion
        if self.capacidad > 20: subtotal += 80000
        return round(subtotal * (1 - descuento) * (1 + impuesto), 2)
    def describir(self): return f"[Sala] {self._nombre} - Capacidad: {self.capacidad} - ${self._precio_base}/hora"

# ---------- CLASE RESERVA ----------
class Reserva:
    def __init__(self, id_reserva, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente): raise DatoInvalidoError("Cliente invalido para la reserva.")
        if not isinstance(servicio, Servicio): raise DatoInvalidoError("Servicio invalido para la reserva.")
        if duracion <= 0: raise ReservaInvalidaError("La duracion debe ser mayor a 0.")
        if not servicio.disponible: raise ServicioNoDisponibleError(f"Servicio '{servicio.nombre}' no disponible.")
        self.id = id_reserva; self.cliente = cliente; self.servicio = servicio
        self.duracion = duracion; self.estado = "Pendiente"; self.costo = 0
    def confirmar(self):
        try:
            if self.estado != "Pendiente": raise OperacionNoPermitidaError(f"No se puede confirmar una reserva en estado {self.estado}.")
            self.costo = self.servicio.calcular_costo(self.duracion)
            self.estado = "Confirmada"
            return f"Reserva {self.id} CONFIRMADA - Costo: ${self.costo}"
        except Exception as e:
            registrar_log(f"Error al confirmar reserva {self.id}: {e}"); raise
    def cancelar(self):
        try:
            if self.estado == "Cancelada": raise OperacionNoPermitidaError("La reserva ya esta cancelada.")
            if self.estado == "Procesada": raise OperacionNoPermitidaError("No se puede cancelar una reserva ya procesada.")
            self.estado = "Cancelada"; return f"Reserva {self.id} CANCELADA."
        except Exception as e:
            registrar_log(f"Error al cancelar reserva {self.id}: {e}"); raise
    def procesar(self):
        try:
            if self.estado != "Confirmada": raise OperacionNoPermitidaError(f"Solo se puede procesar una reserva Confirmada. Estado: {self.estado}.")
            self.estado = "Procesada"; return f"Reserva {self.id} PROCESADA - Servicio entregado a {self.cliente.nombre}."
        except Exception as e:
            registrar_log(f"Error al procesar reserva {self.id}: {e}"); raise

# ---------- SISTEMA ----------
class SistemaF1:
    def __init__(self):
        self.clientes = []; self.servicios = []; self.reservas = []
    def agregar_cliente(self, cliente): self.clientes.append(cliente); print(f"OK - {cliente.mostrar_info()}")
    def agregar_servicio(self, servicio): self.servicios.append(servicio); print(f"OK - {servicio.describir()}")
    def buscar_cliente(self, id_cliente):
        for c in self.clientes:
            if c.id == id_cliente: return c
        raise ClienteNoEncontradoError(f"Cliente con ID {id_cliente} no encontrado.")
    def buscar_servicio(self, id_servicio):
        for s in self.servicios:
            if s.id == id_servicio: return s
        raise ServicioNoDisponibleError(f"Servicio con ID {id_servicio} no encontrado.")

# ---------- SIMULACION: 12 OPERACIONES COMPLETAS ----------
def main():
    sistema = SistemaF1()
    print("=== SOFTWARE F1 - INICIO ===")
    def ejecutar(numero, descripcion, funcion):
        print(f"\n--- Operacion {numero}: {descripcion} ---")
        try:
            resultado = funcion()
            if resultado: print(resultado)
        except DatoInvalidoError as e: print(f"Error controlado DatoInvalido: {e}"); registrar_log(f"Op {numero} DatoInvalido: {e}")
        except ClienteNoEncontradoError as e: print(f"Error controlado Cliente: {e}"); registrar_log(f"Op {numero} Cliente: {e}")
        except ServicioNoDisponibleError as e: print(f"Error controlado Servicio: {e}"); registrar_log(f"Op {numero} Servicio: {e}")
        except ReservaInvalidaError as e: print(f"Error controlado Reserva: {e}"); registrar_log(f"Op {numero} Reserva: {e}")
        except OperacionNoPermitidaError as e: print(f"Error controlado Operacion: {e}"); registrar_log(f"Op {numero} Operacion: {e}")
        except Exception as e: print(f"Error inesperado: {e}"); registrar_log(f"Op {numero} Inesperado: {e}")
        else: print("Operacion exitosa (else).")
        finally: print("Fin operacion (finally).")
    ejecutar(1, "Registrar cliente valido", lambda: sistema.agregar_cliente(Cliente(1, "Ana Perez", "ana@correo.com", "3001234567")))
    ejecutar(2, "Registrar cliente valido 2", lambda: sistema.agregar_cliente(Cliente(2, "Carlos Ruiz", "carlos@correo.com", "3109876543")))
    ejecutar(3, "Registrar cliente invalido - correo sin @", lambda: sistema.agregar_cliente(Cliente(3, "Error", "correo-mal", "123")))
    ejecutar(4, "Crear AlquilerEquipo", lambda: sistema.agregar_servicio(AlquilerEquipo(101, "Proyector 4K", 80000, "Proyector")))
    ejecutar(5, "Crear AsesoriaEspecializada", lambda: sistema.agregar_servicio(AsesoriaEspecializada(102, "Asesoria Redes", 120000, "Ing. Lopez")))
    ejecutar(6, "Crear ReservaSala", lambda: sistema.agregar_servicio(ReservaSala(103, "Sala Conferencias", 150000, 30)))
    def op7():
        r = Reserva(1001, sistema.buscar_cliente(1), sistema.buscar_servicio(101), 2)
        sistema.reservas.append(r); return r.confirmar()
    ejecutar(7, "Reserva valida + confirmar", op7)
    ejecutar(8, "Reserva invalida duracion 0", lambda: Reserva(1002, sistema.buscar_cliente(1), sistema.buscar_servicio(101), 0))
    ejecutar(9, "Reserva con cliente no encontrado", lambda: Reserva(1003, sistema.buscar_cliente(99), sistema.buscar_servicio(101), 1))
    def op10():
        s = sistema.buscar_servicio(102); s.disponible = False
        return Reserva(1004, sistema.buscar_cliente(2), s, 1)
    ejecutar(10, "Reserva con servicio no disponible", op10)
    def op11():
        r = sistema.reservas[0]
        print(r.cancelar())
        try: print(r.procesar())
        except OperacionNoPermitidaError as e: print(f"Error encadenado controlado: {e}")
    ejecutar(11, "Cancelar y luego intentar procesar", op11)
    def op12():
        s = sistema.buscar_servicio(103)
        return f"Costo Sala con descuento 10%: ${s.calcular_costo(3, descuento=0.10)} | Con opciones: ${s.calcular_costo_con_opciones(3, descuento=0.10, recargo_nocturno=20000)}"
    ejecutar(12, "Calcular costos con variantes (metodo sobrecargado)", op12)
    print("\n=== FIN - El sistema siguio funcionando pese a los errores ===")
    print("Revisa el archivo errores.log")

if __name__ == "__main__":
    main()
