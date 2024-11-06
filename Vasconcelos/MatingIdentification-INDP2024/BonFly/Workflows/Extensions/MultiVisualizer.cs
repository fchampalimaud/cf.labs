using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using OpenCV.Net;
using Bonsai.Vision;

[Combinator]
[Description("Isto fas visualizadires ")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class MultiVisualizer
{
    [Description("Method to use for comparing pixels. Darkest maintains the darkest values for each pixel. Brightest maintains the brightest values for each pixel.")]
    public int RadiusSize { get; set; } 
    //public Scalar[] Collors { get; set; }
    Scalar ScalarHSV2BGR(double H, double S, double V) 
    {
        Mat rgb = new Mat(1,1, Depth.U8, 3);
        Mat hsv = new Mat(1,1, Depth.U8, 3);
        hsv[0] = Scalar.Rgb(V,S,H);
        CV.CvtColor(hsv, rgb, ColorConversion.Hsv2Bgr);
        return rgb[0];
    }
    public IObservable<IplImage> Process(IObservable<Tuple<IplImage, Point2f[]>> source)
    {
        return source.Select(value => 
        {
            //var output = value.Item1.Clone();
            var image = value.Item1;
            var output = new IplImage(image.Size,image.Depth, 3);
            CV.CvtColor(image, output,ColorConversion.Gray2Bgr);
            
            int step = 180/value.Item2.Length;
            for (int i = 0; i < value.Item2.Length; i++)
            {
                CV.Circle(output, new Point(value.Item2[i]), RadiusSize, ScalarHSV2BGR(i*step,255,255), 2);
            }
            
            return output;

        });
    }
}
