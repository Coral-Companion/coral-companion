from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .metrics import compute_metrics
from .metrics import Metric

def metric_table(metrics_a: dict, metrics_b: dict):

    groups = []

    for group in metrics_a:
        rows = []
        for key in metrics_a[group]:
            value_a = metrics_a[group][key]
            value_b = metrics_b[group][key]

            if isinstance(value_a, float):
                delta = value_b - value_a
                ratio_percentage = 100 * (1 - value_a / value_b)
            else:
                delta = ""
                ratio_percentage = ""

            rows.append({
                "name": key,
                "before": value_a,
                "after": value_b,
                "delta": delta,
                "ratio_percentage": ratio_percentage,
            })

        groups.append({
            "name": group,
            "rows": rows
        })

    return groups


def build_context(image_a, image_b):

    metrics_a = compute_metrics(image_a)
    metrics_b = compute_metrics(image_b)

    return {

        "metrics": metric_table(
            metrics_a,
            metrics_b,
        ),

        "figures": {

            "images": "images.png",

            "histogram": "brightness_histogram.png",

            "lab": "lab_scatter.png",

            "sobel_before": "sobel_before.png",
            "sobel_after": "sobel_after.png",

            "laplacian_before": "laplacian_before.png",
            "laplacian_after": "laplacian_after.png",

            "brightness_difference": "brightness_difference.png",

            "texture_difference": "texture_difference.png",
        },
        
        "metric_explanations" : {
            Metric.AREA_PIXELS.value:
                "Number of pixels classified as belonging to the coral area. Useful for tracking changes in visible coral size, but affected by cropping, camera distance and perspective.",

            Metric.MEAN_L.value:
                "'Overall, is this coral becoming lighter or darker?': Average LAB L value of the coral area. The L channel represents perceived brightness, making this useful for detecting overall lightness changes. 0=Black, 255=white",

            Metric.MEDIAN_L.value:
                "'Ignoring a few unusually bright or dark spots, what does most of the coral look like?': Middle LAB L brightness value of the coral area. Less affected by extreme bright or dark pixels than the mean and often provides a more robust brightness estimate. 0=Black, 255=white",

            Metric.STD_L.value:
                "'Does the coral have a uniform appearance, or are there strong contrasts between dark and bright areas?': Standard deviation of LAB L brightness values. Higher values indicate greater variation between darker and brighter coral regions.",

            Metric.P5_L.value:
                "'Only 5%% of the pixels are darker': 5th percentile of LAB L values. Represents the darker end of the coral brightness distribution, excluding the darkest few pixels.",

            Metric.P10_L.value:
                "'Only 10%% of the pixels are darker': 10th percentile of LAB L values. Describes the lower brightness range of the coral and helps detect shifts towards darker tissue areas.",

            Metric.P15_L.value:
                "'15%% of the pixels are darker': 15th percentile of LAB L values. Captures the lower brightness region of the coral while reducing sensitivity to extreme pixels.",

            Metric.P25_L.value:
                "'25%% of the pixels are darker': 25th percentile of LAB L values. Represents the lower quarter of the coral brightness distribution.",

            Metric.P75_L.value:
                "'25%% of the pixels are brighter': 75th percentile of LAB L values. Represents the upper quarter of the coral brightness distribution.",

            Metric.P85_L.value:
                "'15%% of the pixels are brighter': 85th percentile of LAB L values. Captures brighter coral regions while reducing sensitivity to isolated highlights.",

            Metric.P90_L.value:
                "'Only 10%% of the pixels are brighter': 90th percentile of LAB L values. Represents the brighter end of the coral brightness distribution.",

            Metric.P95_L.value:
                "'5%% of the pixels are brighter': '95th percentile of LAB L values. Captures the brightest coral regions while avoiding influence from only the most extreme pixels. If this increases heavily, there might be a lot of bleaching",

            Metric.DYNAMIC_RANGE_L.value:
                "'How wide is the brightness distribution? How much contrast exists within the coral?': Difference between the brightest and darkest coral pixels in the LAB L channel. Indicates the range of perceived brightness within the coral tissue. Calculated by 95th Percentile - 5th Percentile. Small=Everything roughly same brightness. Large=eg. Dark Crevices, bright tops",

            Metric.MEAN_A.value:
                "'How green/red is the image?': Average LAB a-channel value. Represents the green-to-red colour axis with negative numbers=greenish, positive numbers=redish. Changes may indicate shifts in coral pigmentation or imaging conditions.",

            Metric.MEAN_B.value:
                "'How blue/yellow is the image?': Average LAB b-channel value. Represents the blue-to-yellow colour axis with negative numbers=blueish, positive numbers=yellowish. Changes may indicate shifts in coral pigmentation or environmental appearance.",

            Metric.STD_A.value:
                "'Is the coral uniformly coloured, or does it contain patches with different colour tones?': Standard deviation of LAB a-channel values. Measures variation along the green-red colour axis.",

            Metric.STD_B.value:
                "'Is the coral uniformly coloured, or does it contain patches with different colour tones?': Standard deviation of LAB b-channel values. Measures variation along the blue-yellow colour axis.",

            Metric.SOBEL_MEAN.value:
                "Average Sobel gradient magnitude. Measures overall edge strength and structural complexity within the coral image. Changes between coral images can indicate its texture is smoothening (or that the image is not sharp)",

            Metric.SOBEL_MEDIAN.value:
                "Median Sobel gradient magnitude. Represents the typical edge strength while being less affected by isolated sharp boundaries. Changes between coral images can indicate its texture is smoothening (or that the image is not sharp)",

            Metric.SOBEL_P95.value:
                "95th percentile of Sobel gradient magnitude. Highlights the strongest edges and fine structural details present in the coral. This is interesting because it captures the crispiest structural features",

            Metric.SOBEL_STD.value:
                "Standard deviation of Sobel gradient magnitude. Measures how variable the structural complexity is across the coral surface. Low values=smooth overall. High values=Lots of textural changes",
            
            Metric.LAPLACIAN_VARIANCE.value:
                "Measures variation in the Laplacian response, which captures fine intensity changes. Higher values usually indicate more small-scale structural detail or texture. Also subject to sharpness of coral image.",
        }
    }


def create_report(
    image_a,
    image_b,
    output_directory: Path,
):

    env = Environment(
        loader=FileSystemLoader(
            Path(__file__).parent / "templates"
        )
    )

    template = env.get_template("report.html")

    context = build_context(
        image_a,
        image_b,
    )

    html = template.render(context)

    report = output_directory / "report.html"

    report.write_text(
        html,
        encoding="utf-8",
    )

    return report