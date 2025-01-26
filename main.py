import asyncio
from bleak import BleakClient, BleakError
from datetime import datetime

# Adres MAC urządzenia Bluetooth LE
DEVICE_MAC_ADDRESS = "3C:A3:08:AA:00:2C"

# UUID dla serwisu i charakterystyki (upewnij się, że są poprawne dla Twojego urządzenia)
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"  # Przykład UUID serwisu
CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Przykład UUID charakterystyki

# Zmienna globalna do przechowywania wartości
data_buffer = None



# Funkcja obsługi notyfikacji, odbioru danych
def notification_handler(sender, data):
    global data_buffer
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    message = data.decode("utf-8").strip()


    # Łączenie danych z poprzednią częścią, jeśli istnieje bufor
    if data_buffer:
        message = f"{data_buffer},{message}"
        data_buffer = None

    # Sprawdzanie, czy dane są kompletne
    if message.count(",") < 4:  # Zakładam, że kompletne dane mają 4 wartości oddzielone przecinkami
        data_buffer = message  # Zapis do bufora, aby połączyć z kolejnymi danymi
        print("Dane sa kompletne")
        return

    try:
        # Zapis do pliku
        with open("/root/Desktop/venv/venv/data.txt", "a") as file:
            file.write(f"{timestamp},{message}\n")

        # Usunięcie nadmiarowych przecinków
        while ',,' in message:
            message = message.replace(',,', ',')
            print(f"Otrzymano dane: {timestamp},{message}")
            print("Oczekiwanie na dane...")
    except Exception as e:
        print(f"Błąd podczas zapisu do pliku: {e}")






# Funkcja do łączenia się z Bluetooth
async def connect_device():
    while True:
        try:
            print(f"Łączenie z urządzeniem {DEVICE_MAC_ADDRESS}...")
            client = BleakClient(DEVICE_MAC_ADDRESS)

            # Próba nawiązania połączenia
            await client.connect()

            # Sprawdzanie, czy połączenie się powiodło
            if client.is_connected:
                print(f"Połączono z urządzeniem {DEVICE_MAC_ADDRESS}")
                return client

        except BleakError as e:
            print(f"Nie udało się połączyć z urządzeniem: {e}")

        except asyncio.TimeoutError:
            print("Połączenie Bluetooth przekroczyło limit czasu!")

        # Zapytanie użytkownika, czy chce spróbować ponownie
        print("\n--- MENU ŁĄCZENIA ---")
        print("1: Spróbuj ponownie")
        print("0: Powrót do menu głównego")
        choice = input("Wybierz opcję: ").strip()

        if choice == "0":
            print("Przerwano próbę połączenia.")
            return None


async def main():
    client = None
    while True:
        print("\n--- MENU GŁÓWNE ---")
        print("1: Połącz z urządzeniem Bluetooth")
        print("2: Sterowanie (wysyłanie danych)")
        print("3: Odbiór danych (notyfikacje)")
        print("0: Wyjście")
        choice = input("Wybierz opcję: ")

        if choice == "1":
            client = await connect_device()

        elif choice == "2":
            if client and client.is_connected:
                while True:
                    message = input("Wpisz wiadomość do wysłania ('exit' aby wrócić do menu): ")
                    if message.lower() == "exit":
                        break
                    try:
                        await client.write_gatt_char(CHARACTERISTIC_UUID, message.encode("utf-8"))
                        print(f"Wysłano: {message}")
                    except BleakError as e:
                        print(f"Błąd podczas wysyłania danych: {e}")
            else:
                print("Najpierw połącz się z urządzeniem Bluetooth.")

        elif choice == "3":
            if client and client.is_connected:
                try:
                    print("Subskrypcja powiadomień. Wciśnij Ctrl+C, aby zakończyć odbiór danych.")
                    await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
                    try:
                        while True:
                            await asyncio.sleep(1)
                    except KeyboardInterrupt:
                        print("\nPrzerwano odbiór danych.")
                    finally:
                        await client.stop_notify(CHARACTERISTIC_UUID)
                        print("Zatrzymano subskrypcję powiadomień.")
                except BleakError as e:
                    print(f"Błąd podczas subskrypcji powiadomień: {e}")
            else:
                print("Najpierw połącz się z urządzeniem Bluetooth.")

        elif choice == "0":
            if client and client.is_connected:
                await client.disconnect()
                print("Rozłączono urządzenie.")
            print("Zakończono program.")
            break

        else:
            print("Niepoprawny wybór. Spróbuj ponownie.")

# Uruchomienie programu
if __name__ == "__main__":
    asyncio.run(main())
