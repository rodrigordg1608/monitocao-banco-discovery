"""Registra um diagnóstico orientativo para a falha intencional do laboratório.

Em uma implementação real, este script poderia receber o trecho saneado do log por
uma variável protegida e enviá-lo a um modelo aprovado pela organização.
"""

DIAGNOSIS = """
Diagnóstico da falha:
O teste fornece minimum_balance como texto (\"250.0\"), enquanto balance é float.
A função calculate_alert_threshold subtrai esses valores diretamente, gerando:
TypeError: unsupported operand type(s) for -: 'float' and 'str'.

Correção sugerida:
Converter minimum_balance para float antes da operação ou validar/converter a
entrada na borda da aplicação. Depois, executar pytest novamente para confirmar
que a correção não introduziu regressões.
""".strip()


if __name__ == "__main__":
    print(DIAGNOSIS)
