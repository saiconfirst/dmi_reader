from dmi_reader import get_dmi_info

if __name__ == "__main__":
    print("Получаем DMI информацию...")
    info = get_dmi_info(include_fallback=True)
    print("DMI Data:", info)