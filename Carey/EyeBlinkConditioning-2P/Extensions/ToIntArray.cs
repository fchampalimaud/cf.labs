using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;

[Combinator]
[Description("")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class ToIntArray
{
    public IObservable<int[]> Process(IObservable<double[]> source)
    {
        return source.Select(value => {
            int[] output = new int[value.Length];

            for(int i=0; i<value.Length; i++)
            {
                output[i] = (int) Math.Round(value[i]);
            }
            return output;
        });
    }
}
