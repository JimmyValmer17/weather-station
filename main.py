import asyncio
from bleak import BleakClient, BleakError
from datetime import datetime

# Adres MAC urzadzenia Bluetooth LE
DEVICE_MAC_ADDRESS = "3C:A3:08:AA:00:2C"

# UUID dla serwisu i charakterystyki (upewnij sie, ze sa poprawne dla Twojego urzadzenia)
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"  # Przyklad UUID serwisu
CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Przyklad UUID charakterystyki

# Zmienna globalna do przechowywania wartosci
data_buffer = None


# Funkcja obslugi notyfikacji
def notification_handler(sender, data):
    global data_buffer
    # Pobranie aktualnej daty i godziny w formacie YYYYMMDDHHMMSS
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    message = data.decode("utf-8")

    # Jesli dane to wartosci temperatury, wilgotnosci i cisnienia (np. "21.18,28.95,1029.91")
    if ',' in message:
        # Jesli mamy juz zapisany ostatni odczyt temperatury/wilgotnosci/cisnienia, zapisujemy je w jednej linii
        if data_buffer:
            # Laczenie danych w jednej linii
            data_values = message.split(',')
            data_values = [val.strip() for val in data_values if val.strip()]  # Usuwamy puste wartosci
            message = ','.join(data_values)  # Laczymy wartosci w jedna linie

            # Zastepujemy podwójne przecinki jednym
            message = message.replace(',,', ',')

            # Jesli wciaz wystepuja podwójne przecinki, usuwamy je
            while ',,' in message:
                message = message.replace(',,', ',')

            # Otwieranie pliku w trybie dopisywania
            try:
                with open("data.txt", "a") as file:
                    file.write(f"{timestamp},{message}\n")
                print(f"Otrzymano dane: {timestamp},{message}")
                data_buffer = None  # Resetowanie bufora po zapisaniu
            except Exception as e:
                print(f"Blad podczas zapisu do pliku: {e}")
        else:
            # Jesli nie mamy jeszcze wartosci temperatury/wilgotnosci/cisnienia, zapisujemy do bufora
            data_buffer = message
    else:
        # Jesli dane to np. wartosc "3.57", zapisujemy je jako czesc bufora
        if data_buffer:
            message = f"{data_buffer},{message}"
            data_buffer = None  # Resetowanie bufora po zapisaniu
            # Otwieranie pliku w trybie dopisywania
            try:
                with open("data.txt", "a") as file:
                    file.write(f"{timestamp},{message}\n")
                print(f"Otrzymano dane: {timestamp},{message}")
            except Exception as e:
                print(f"Blad podczas zapisu do pliku: {e}")
        else:
            # Jesli nie mamy jeszcze pelnych danych, ignorujemy lub czekamy na nastepne
            print("Oczekiwanie na pelne dane...")


async def main():
    async with BleakClient(DEVICE_MAC_ADDRESS) as client:
        if not client.is_connected:
            print("Nie udalo sie polaczyc z urzadzeniem!")
            return

        print(f"Polaczono z urzadzeniem {DEVICE_MAC_ADDRESS}")

        while True:
            print("\n--- MENU ---")
            print("1: Sterowanie (wysylanie danych)")
            print("2: Odbiór danych (notyfikacje)")
            print("0: Wyjscie")
            choice = input("Wybierz opcje: ")

            if choice == "1":
                # Sterowanie - wysylanie danych
                while True:
                    message = input("Wpisz wiadomosc do wyslania ('exit' aby wrócic do menu): ")
                    if message.lower() == "exit":
                        break
                    try:
                        await client.write_gatt_char(CHARACTERISTIC_UUID, message.encode("utf-8"))
                        print(f"Wyslano: {message}")
                    except BleakError as e:
                        print(f"Blad podczas wysylania danych: {e}")

            elif choice == "2":
                # Odbiór danych - subskrypcja notyfikacji
                try:
                    print("Subskrypcja powiadomien. Wcisnij Ctrl+C, aby zakonczyc odbiór danych.")

                    await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

                    try:
                        # Petla dziala dopóki uzytkownik nie zakonczy programu
                        while True:
                            await asyncio.sleep(1)
                    except KeyboardInterrupt:
                        print("\nPrzerwano odbiór danych.")
                    finally:
                        await client.stop_notify(CHARACTERISTIC_UUID)
                        print("Zatrzymano subskrypcje powiadomien.")

                except BleakError as e:
                    print(f"Blad podczas subskrypcji powiadomien: {e}")

            elif choice == "0":
                print("Zakonczono program.")
                break

            else:
                print("Niepoprawny wybór. Spróbuj ponownie.")


# Uruchomienie programu
if __name__ == "__main__":
    asyncio.run(main())
