import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime
st.title("🎈 Анализ погоды ")
st.write(
    "Загрузите пожалуйста файлллл"
)
uploaded_file = st.file_uploader("Загрузите CSV-файл с историческими данными", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
    
    required_columns = {'timestamp', 'city', 'temperature'}
    if not required_columns.issubset(df.columns):
        st.error(f"Ошибка: CSV-файл должен содержать столбцы: {', '.join(required_columns)}")
    else:
        cities = df['city'].unique()
        selected_city = st.selectbox('Выберите город', cities)
        
        city_data = df[df['city'] == selected_city]
        st.header('Описательная статистика')
        st.write(city_data['temperature'].describe())
        st.header('Временной ряд температур с аномалиями')
        city_data = city_data.sort_values('timestamp')
        city_data.set_index('timestamp', inplace=True)
        rolling_mean = city_data['temperature'].rolling(window=30, center=True).mean()
        rolling_std = city_data['temperature'].rolling(window=30, center=True).std()
        anomalies = city_data[(city_data['temperature'] > rolling_mean + 2 * rolling_std) | 
                              (city_data['temperature'] < rolling_mean - 2 * rolling_std)]

        plt.figure(figsize=(10,5))
        plt.plot(city_data.index, city_data['temperature'], label='Температура')
        plt.scatter(anomalies.index, anomalies['temperature'], color='red', label='Аномалии')
        plt.legend()
        st.pyplot(plt.gcf())

        st.header('Сезонные профили')
        city_data['month'] = city_data.index.month
        monthly_stats = city_data.groupby('month')['temperature'].agg(['mean', 'std'])
        plt.figure(figsize=(10,5))
        plt.errorbar(monthly_stats.index, monthly_stats['mean'], yerr=monthly_stats['std'], fmt='o', capsize=5)
        plt.xticks(range(1,13))
        plt.xlabel('Месяц')
        plt.ylabel('Температура')
        plt.title('Сезонный профиль температуры')
        st.pyplot(plt.gcf())

        api_key = st.text_input('Введите API-ключ OpenWeatherMap', type='password')
        if api_key:
            try:
                geocode_url = f'http://api.openweathermap.org/geo/1.0/direct?q={selected_city}&limit=1&appid={api_key}'
                geocode_response = requests.get(geocode_url)
                if geocode_response.status_code == 200:
                    geocode_data = geocode_response.json()
                    if geocode_data:
                        lat = geocode_data[0]['lat']
                        lon = geocode_data[0]['lon']

                        # Запрос текущей погоды
                        weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
                        weather_response = requests.get(weather_url)
                        if weather_response.status_code == 200:
                            weather_data = weather_response.json()
                            current_temp = weather_data['main']['temp']
                            st.success(f'Текущая температура в городе {selected_city}: {current_temp}°C')

                            # Проверка, нормальна ли температура для сезона
                            current_month = datetime.datetime.now().month
                            if current_month in monthly_stats.index:
                                
                                monthly_mean = monthly_stats.loc[current_month, 'mean']
                                monthly_std = monthly_stats.loc[current_month, 'std']

                                if abs(current_temp - monthly_mean) <= monthly_std:
                                    st.info('Текущая температура нормальна для этого месяца.')
                                else:
                                    st.warning('Текущая температура аномальна для этого месяца.')
                            else:
                                st.info('Нет данных для текущего месяца для сравнения.')
                        elif weather_response.status_code == 401:
                            st.error('Ошибка 401: Неверный API-ключ.')
                        else:
                            st.error(f'Ошибка при получении текущей погоды: {weather_response.status_code}')
                    else:
                        st.error('Не удалось получить данные геокодирования. Проверьте название города.')
                elif geocode_response.status_code == 401:
                    st.error('Ошибка 401: Неверный API-ключ.')
                else:
                    st.error(f'Ошибка при геокодировании: {geocode_response.status_code}')
            except Exception as e:
                st.error(f'Произошла ошибка: {e}')
        else:
            st.info('Введите API-ключ для получения текущей температуры.')
else:
    st.info('Пожалуйста, загрузите CSV-файл с историческими данными.')
