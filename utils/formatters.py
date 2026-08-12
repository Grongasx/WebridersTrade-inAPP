"""
Formatadores e formatadores de moeda.
"""

import re


class CurrencyFormatter:
    """Gerencia formatacao de moeda em tempo real para widgets Entry."""
    
    @staticmethod
    def mascara_moeda_dinamica(entry):
        """Aplica mascara de moeda em um widget Entry."""
        digits = re.sub(r"\D", "", entry.get())
        if not digits or int(digits) == 0:
            fmt = "0,00"
        else:
            fmt = f"{int(digits)/100:,.2f}".replace(",","X").replace(".",",").replace("X",".")
        entry.delete(0, "end")
        entry.insert(0, fmt)
    
    @staticmethod
    def formatar_moeda_entry(event, entry):
        """Handler de evento KeyRelease para formatacao de moeda."""
        if event and event.keysym in ("Left","Right","Up","Down","Shift_L","Shift_R","Tab","Return"):
            return
        digits = re.sub(r"\D", "", entry.get())
        if not digits:
            digits = "0"
        fmt = f"R$ {int(digits)/100:,.2f}".replace(",","X").replace(".",",").replace("X",".")
        entry.delete(0, "end")
        entry.insert(0, fmt)
    
    @staticmethod
    def formatar_moeda_local(entry):
        """Formata moeda sem prefixo R$."""
        d = re.sub(r"\D", "", entry.get())
        if not d:
            fmt = "0,00"
        else:
            fmt = f"{int(d)/100:,.2f}".replace(",","X").replace(".",",").replace("X",".")
        entry.delete(0, "end")
        entry.insert(0, fmt)