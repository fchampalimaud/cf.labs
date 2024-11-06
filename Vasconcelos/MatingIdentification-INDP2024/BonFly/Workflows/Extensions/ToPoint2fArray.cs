using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using OpenCV.Net;

[Combinator]
[Description("")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class ToPoint2fArray
{
    public IObservable<Point2f[]> Process(IObservable<float[]> source)
    {
        return source.Select(value =>
        {
            var result = new Point2f[value.Length/2];
            var count =0;
            for (int i = 0; i < result.Length; i++)
            {
                result[i] = new Point2f(value[count], value[count+1]);
                count +=2;
            }
            return result;
        });
    }
}
