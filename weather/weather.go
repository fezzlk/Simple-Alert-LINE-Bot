package weather

import (
    "os"
    "fmt"
    "encoding/json"
    "io/ioutil"
    "net/http"
)

// OpenWeather api (https://openweathermap.org/current) を使って天気情報を取得
func GetWeather() []Result {
    // GET リクエストを投げる
    apiKey := os.Getenv("OPEN_WEATHER_MAP_API_KEY")
    cityName := "Yokohama"
    url := fmt.Sprintf("http://api.openweathermap.org/data/2.5/forecast?q=%s&appid=%s&lang=ja&units=metric", cityName, apiKey)
    res, err := http.Get(url)
    if err != nil {
        panic(err)
    }

    defer res.Body.Close() 

    // レスポンス表示
    body, err := ioutil.ReadAll(res.Body)
    if err != nil{
        panic(err)
    }

    // jsonを構造体へデコード
    var data Response
    if err := json.Unmarshal(body, &data); err != nil {
        panic(err)
    }
    
    var result []Result 
    for _, d := range data.List {
        var r Result
        r.Date = d.DtTxt
        r.Temp = d.Main.Temp
        r.Weather = d.Weather[0].Description
        result = append(result, r)
    }

    // fmt.Printf("%v", result)
    return result
}

// getWeather関数の戻り値
type Result struct {
    Date	string	`json:"date"`
    Temp	float64	`json:"temp"`
    Weather	string	`json:"weather"` 
}

// 自動生成 by https://mholt.github.io/json-to-go/
type Response struct {
    Cod     string `json:"cod"`
    Message int    `json:"message"`
    Cnt     int    `json:"cnt"`
    List    []struct {
        Dt   int `json:"dt"`
        Main struct {
            Temp      float64 `json:"temp"`
            FeelsLike float64 `json:"feels_like"`
            TempMin   float64 `json:"temp_min"`
            TempMax   float64 `json:"temp_max"`
            Pressure  int     `json:"pressure"`
            SeaLevel  int     `json:"sea_level"`
            GrndLevel int     `json:"grnd_level"`
            Humidity  int     `json:"humidity"`
            TempKf    float64 `json:"temp_kf"`
        } `json:"main"`
        Weather []struct {
            ID          int    `json:"id"`
            Main        string `json:"main"`
            Description string `json:"description"`
            Icon        string `json:"icon"`
        } `json:"weather"`
        Clouds struct {
            All int `json:"all"`
        } `json:"clouds"`
        Wind struct {
            Speed float64 `json:"speed"`
            Deg   int     `json:"deg"`
            Gust  float64 `json:"gust"`
        } `json:"wind"`
        Visibility int     `json:"visibility"`
        Pop        float64 `json:"pop"`
        Rain       struct {
            ThreeH float64 `json:"3h"`
        } `json:"rain,omitempty"`
        Sys struct {
            Pod string `json:"pod"`
        } `json:"sys"`
        DtTxt string `json:"dt_txt"`
    } `json:"list"`
    City struct {
        ID    int    `json:"id"`
        Name  string `json:"name"`
        Coord struct {
            Lat float64 `json:"lat"`
            Lon float64 `json:"lon"`
        } `json:"coord"`
        Country    string `json:"country"`
        Population int    `json:"population"`
        Timezone   int    `json:"timezone"`
        Sunrise    int    `json:"sunrise"`
        Sunset     int    `json:"sunset"`
    } `json:"city"`
}