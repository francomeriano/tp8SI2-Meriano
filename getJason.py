"""
Sistema de pagos automatizado - Versión 1.2
TP8 - Ingeniería Reversa, Refactoría y Reingeniería
"""
import json
from typing import List, Optional
from abc import ABC, abstractmethod

# 1. SINGLETON (ya existente) - Configurador
class Configurador:
    """Singleton que carga la configuración desde sitedata.json"""
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._cargar_config()
        return cls._instancia

    def _cargar_config(self):
        with open("sitedata.json", "r", encoding="utf-8") as f:
            self.datos = json.load(f)

    def obtener_clave(self, token: str) -> Optional[str]:
        """Retorna la clave para un token dado"""
        return self.datos.get(token)


# 2. MODELO: Cuenta / Banco
class Cuenta:
    """Representa una cuenta bancaria con saldo"""
    def __init__(self, token: str, saldo_inicial: float):
        self.token = token
        self.clave = Configurador().obtener_clave(token)
        self.saldo = saldo_inicial

    def pagar(self, monto: float) -> bool:
        """Intenta debitar el monto. Retorna True si se pudo."""
        if self.saldo >= monto:
            self.saldo -= monto
            return True
        return False


# 3. CHAIN OF RESPONSIBILITY
class ManejadorPago(ABC):
    """Clase base para la cadena de responsabilidad"""
    def __init__(self, cuenta: Cuenta):
        self.cuenta = cuenta
        self.siguiente: Optional[ManejadorPago] = None

    def set_siguiente(self, manejador: 'ManejadorPago') -> 'ManejadorPago':
        self.siguiente = manejador
        return manejador

    @abstractmethod
    def manejar(self, pedido: 'PedidoPago') -> bool:
        """Intenta manejar el pedido. Retorna True si se procesó."""
        pass


class ManejadorConcreto(ManejadorPago):
    """Manejador concreto para una cuenta específica"""
    def manejar(self, pedido: 'PedidoPago') -> bool:
        if self.cuenta.pagar(pedido.monto):
            pedido.token_usado = self.cuenta.token
            pedido.estado = "APROBADO"
            return True
        if self.siguiente:
            return self.siguiente.manejar(pedido)
        return False



# 4. PEDIDO DE PAGO

class PedidoPago:
    """Representa una solicitud de pago"""
    def __init__(self, nro_pedido: int, monto: float):
        self.nro_pedido = nro_pedido
        self.monto = monto
        self.token_usado: Optional[str] = None
        self.estado: str = "RECHAZADO"



# 5. REGISTRO DE PAGOS (ITERATOR)

class RegistroPagos:
    """Almacena los pagos realizados en orden cronológico"""
    def __init__(self):
        self._pagos: List[PedidoPago] = []

    def agregar(self, pedido: PedidoPago):
        self._pagos.append(pedido)

    def __iter__(self):
        return iter(self._pagos)

    def listar(self):
        """Muestra todos los pagos por orden cronológico"""
        print("\n--- LISTADO DE PAGOS (orden cronológico) ---")
        for p in self._pagos:
            print(f"Pedido #{p.nro_pedido}: ${p.monto} - Token: {p.token_usado} - {p.estado}")
        print("----------------------------------------------\n")



# 6. SISTEMA DE PAGOS (integración)
class SistemaPagos:
    """Orquesta el proceso de pago automatizado"""
    def __init__(self):
        # Crear cuentas
        cuenta1 = Cuenta("token1", 1000.0)
        cuenta2 = Cuenta("token2", 2000.0)

        # Construir cadena de responsabilidad
        manejador1 = ManejadorConcreto(cuenta1)
        manejador2 = ManejadorConcreto(cuenta2)
        manejador1.set_siguiente(manejador2)

        self.manejador_inicial = manejador1
        self.registro = RegistroPagos()

    def procesar_pago(self, nro_pedido: int, monto: float) -> str:
        """Procesa un pedido de pago y retorna un mensaje de resultado"""
        pedido = PedidoPago(nro_pedido, monto)
        exito = self.manejador_inicial.manejar(pedido)

        if exito:
            self.registro.agregar(pedido)
            return f"✅ Pago #{nro_pedido} aprobado con {pedido.token_usado}"
        else:
            return f"❌ Pago #{nro_pedido} rechazado - Saldo insuficiente en todas las cuentas"



# 7. DEMOSTRACIÓN Y PRUEBA
def main():
    """Función principal de demostración"""
    sistema = SistemaPagos()

    # Simular pedidos de pago
    pedidos = [1, 2, 3, 4, 5, 6, 7]
    for nro in pedidos:
        resultado = sistema.procesar_pago(nro, 500.0)
        print(resultado)

    # Listar todos los pagos
    sistema.registro.listar()

    # Mostrar saldos finales
    print("--- SALDOS FINALES ---")
    # Obtenemos las cuentas desde la cadena (accedemos al primer manejador)
    manejador = sistema.manejador_inicial
    while manejador:
        print(f"{manejador.cuenta.token}: ${manejador.cuenta.saldo:.2f}")
        manejador = manejador.siguiente


if __name__ == "__main__":
    main()

    