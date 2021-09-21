# Taken from https://github.com/pkucmus/micropython-pms7003 with fixes.
class AQI:
    AQI = (
        (0, 50),
        (51, 100),
        (101, 150),
        (151, 200),
        (201, 300),
        (301, 400),
        (401, 500),
    )

    _PM2_5 = (
        (0, 12),
        (12.1, 35.4),
        (35.5, 55.4),
        (55.5, 150.4),
        (150.5, 250.4),
        (250.5, 350.4),
        (350.5, 500.4),
    )

    @classmethod
    def PM2_5(cls, data):
        return cls._calculate_aqi(cls._PM2_5, data)

    @classmethod
    def _calculate_aqi(cls, breakpoints, data):
        for index, data_range in enumerate(breakpoints):
            if data <= data_range[1]:
                break

        i_low, i_high = cls.AQI[index]
        c_low, c_high = data_range
        # print(f"({i_high} - {i_low}) / ({c_high} - {c_low}) * ({data} - {c_low}) + {i_low}")
        return (i_high - i_low) / (c_high - c_low) * (data - c_low) + i_low

    @classmethod
    def aqi(cls, pm2_5_atm):
        return cls.PM2_5(pm2_5_atm)
