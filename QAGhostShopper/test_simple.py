#!/usr/bin/env python
"""
Script simple para probar que bot.py funciona correctamente.
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import run_ghost_shopper_test

print("\n" + "="*60)
print("PRUEBA SIMPLE DE QA GHOST SHOPPER")
print("="*60)
print("[*] Iniciando test...")

try:
    results = run_ghost_shopper_test('https://www.saucedemo.com')
    
    print("\n" + "="*60)
    print("TEST COMPLETADO")
    print("="*60)
    
    total_steps = len(results)
    print(f"\nTotal de pasos ejecutados: {total_steps}\n")
    
    for result in results:
        step = result['step']
        descripcion = result['descripcion']
        estado = result['estado']
        print(f"   Paso {step}: {descripcion}")
        print(f"   Estado: {estado}\n")
        
except Exception as e:
    print("\n" + "="*60)
    print("ERROR EN LA EJECUCION")
    print("="*60)
    print(f"Error: {str(e)}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*60)
