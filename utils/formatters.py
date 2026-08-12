"""
Formatadores e formatadores de moeda de alta performance.
"""

import re


class CurrencyFormatter:
    """Gerencia formatação de moeda em tempo real com suporte a digitação ultra-fluida."""
    
    @staticmethod
    def mascara_moeda_dinamica(entry):
        """Aplica máscara de moeda sem redesenhos desnecessários."""
        val_atual = entry.get()
        digits = re.sub(r"\D", "", val_atual)
        if not digits or int(digits) == 0:
            fmt = "0,00"
        else:
            fmt = f"{int(digits)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        if val_atual != fmt:
            entry.delete(0, "end")
            entry.insert(0, fmt)
            entry.icursor("end")

    @staticmethod
    def formatar_moeda_entry(event, entry):
        """Handler de evento KeyRelease para formatação de moeda com R$."""
        if event and event.keysym in ("Left", "Right", "Up", "Down", "Shift_L", "Shift_R", "Tab", "Return"):
            return
        val_atual = entry.get()
        digits = re.sub(r"\D", "", val_atual)
        if not digits or int(digits) == 0:
            fmt = "R$ 0,00"
        else:
            fmt = f"R$ {int(digits)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        if val_atual != fmt:
            entry.delete(0, "end")
            entry.insert(0, fmt)
            entry.icursor("end")

    @staticmethod
    def formatar_moeda_local(entry):
        """Formata moeda local sem prefixo R$ mantendo o cursor fluido."""
        val_atual = entry.get()
        digits = re.sub(r"\D", "", val_atual)
        if not digits or int(digits) == 0:
            fmt = "0,00"
        else:
            fmt = f"{int(digits)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        if val_atual != fmt:
            entry.delete(0, "end")
            entry.insert(0, fmt)
            entry.icursor("end")